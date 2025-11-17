"""
Integrated AI Crawler Tracking + URL Content Store Demo
========================================================

This demo leverages the URL_Crawler infrastructure (ContentCrawler, ContentStore)
to crawl and store page content while tracking AI bot activity from bot_table.csv
and server_log.csv.

Features:
- Crawls a website or list of full URLs from a CSV
- Stores normalized content documents using ContentStore
- Tracks which AI bots accessed which pages
- Generates AI bot interaction analytics
- Outputs a unified content store with AI bot metadata

Run with website:
  python3 URL_Crawler/demo_ai_crawler_integrated.py --website https://example.com --limit 10

Run with CSV of URLs:
  python3 URL_Crawler/demo_ai_crawler_integrated.py --csv urls.csv --limit 10

Run with bot/log tracking:
  python3 URL_Crawler/demo_ai_crawler_integrated.py --website https://example.com \
    --bot-table AICrawlerLogging/bot_table.csv --server-log AICrawlerLogging/server_log.csv
"""

import sys
import os
import csv
import json
import argparse
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path
from dataclasses import asdict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Add URL_Crawler to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from crawler import ContentCrawler
from store import ContentStore
from schema import ContentDocument, ContentMetrics, CrawlMetadata, EntityType

class AIBotTracker:
    """Tracks AI bot interactions with crawled content"""
    
    def __init__(self):
        self.bot_interactions = defaultdict(list)  # bot_name -> list of (url, timestamp, status_code)
        self.url_bot_map = defaultdict(set)  # url -> set of bot names
        self.bot_stats = {}
    
    def load_bot_table(self, filepath):
        """Load bot patterns from bot_table.csv"""
        bots = set()
        interactions = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    bot = row.get('Bot') or row.get('bot')
                    url = row.get('Page path') or row.get('Page Path')
                    date = row.get('Date') or row.get('date')
                    status = row.get('Response status codes')
                    
                    if bot and bot != 'Unknown':
                        bots.add(bot)
                        if url:
                            # Normalize path: ensure it starts with /
                            if not url.startswith('/'):
                                url = '/' + url
                            interactions.append({
                                'bot': bot,
                                'url': url,
                                'date': date,
                                'status': status
                            })
        except FileNotFoundError:
            print(f"Warning: {filepath} not found")
        
        return bots, interactions
    
    def load_server_logs(self, filepath, url_limit=None):
        """Load and deduplicate URI paths from server_log.csv"""
        paths = set()
        path_list = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('Page path') or row.get('Page Path') or '/'
                    
                    # Normalize path
                    if not url.startswith('/'):
                        url = '/' + url
                    
                    # Skip empty/unwanted paths
                    if url not in {'/blank', '/'} and url not in paths:
                        paths.add(url)
                        path_list.append(url)
                        if url_limit and len(path_list) >= url_limit:
                            break
        except FileNotFoundError:
            print(f"Warning: {filepath} not found")
        
        return path_list
    
    def add_interaction(self, bot_name, url, timestamp=None, status_code=None):
        """Record a bot interaction"""
        self.bot_interactions[bot_name].append({
            'url': url,
            'timestamp': timestamp or datetime.utcnow().isoformat(),
            'status_code': status_code
        })
        self.url_bot_map[url].add(bot_name)
    
    def get_summary(self):
        """Generate summary of bot activity"""
        summary = {
            'total_unique_bots': len(self.bot_interactions),
            'total_unique_urls_accessed': len(self.url_bot_map),
            'bots': {}
        }
        
        for bot, interactions in self.bot_interactions.items():
            summary['bots'][bot] = {
                'interaction_count': len(interactions),
                'unique_urls': len(set(i['url'] for i in interactions)),
                'status_codes': Counter(i['status_code'] for i in interactions if i['status_code'])
            }
        
        return summary


class IntegratedCrawlerDemo:
    """Main orchestrator for integrated crawling and AI bot tracking"""
    
    def __init__(self, website_url=None, csv_urls=None, bot_table_path=None, server_log_path=None):
        """
        Initialize demo.
        
        Args:
            website_url: Single website to crawl (will enumerate internal links)
            csv_urls: Path to CSV file with full URLs (one per line or in 'url' column)
            bot_table_path: Path to bot_table.csv for tracking
            server_log_path: Path to server_log.csv for tracking
        """
        self.website_url = website_url
        self.csv_urls = csv_urls
        self.bot_table_path = bot_table_path or 'AICrawlerLogging/bot_table.csv'
        self.server_log_path = server_log_path or 'AICrawlerLogging/server_log.csv'
        
        self.crawler = ContentCrawler(crawler_id="ai-bot-tracker-v1")
        self.store = ContentStore(storage_path="ai_crawler_store.json")
        self.tracker = AIBotTracker()
        self.urls_to_crawl = []
    
    def load_urls_from_csv(self, filepath):
        """Load full URLs from CSV file"""
        urls = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Try to detect if it has a header
                sample = f.readline()
                f.seek(0)
                
                # If first line looks like a header, use DictReader, else just read lines
                if 'url' in sample.lower() or 'http' not in sample:
                    reader = csv.DictReader(f)
                    for row in reader:
                        url = row.get('url') or row.get('URL') or row.get('Url')
                        if url and url.startswith('http'):
                            urls.append(url.strip())
                else:
                    # Simple line-by-line read
                    for line in f:
                        line = line.strip()
                        if line.startswith('http'):
                            urls.append(line)
        except FileNotFoundError:
            print(f"Error: CSV file {filepath} not found")
        
        return urls
    
    def load_urls_from_website(self, website_url, limit=10):
        """
        Crawl a website to discover internal URLs.
        This is a simple implementation that extracts links from the homepage.
        """
        urls = [website_url]  # Start with base URL
        visited = {website_url}
        
        try:
            response = requests.get(website_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                full_url = href if href.startswith('http') else urljoin(website_url, href)
                
                # Only keep same-domain URLs
                if urlparse(full_url).netloc == urlparse(website_url).netloc:
                    if full_url not in visited:
                        urls.append(full_url)
                        visited.add(full_url)
                        
                        if len(urls) >= limit:
                            break
        except Exception as e:
            print(f"Warning: Could not crawl website for links: {e}")
        
        return urls[:limit]
    
    def prepare_urls(self, url_limit=10):
        """Prepare list of URLs to crawl based on input"""
        if self.csv_urls:
            print(f"Loading URLs from CSV: {self.csv_urls}")
            self.urls_to_crawl = self.load_urls_from_csv(self.csv_urls)[:url_limit]
        elif self.website_url:
            print(f"Discovering URLs from website: {self.website_url}")
            self.urls_to_crawl = self.load_urls_from_website(self.website_url, limit=url_limit)
        else:
            print("Error: Must provide either --website or --csv")
            return False
        
        print(f"Prepared {len(self.urls_to_crawl)} URLs to crawl")
        for url in self.urls_to_crawl[:3]:
            print(f"  - {url}")
        
        return True
    
    def run(self, url_limit=10):
        """Execute full demo pipeline"""
        print("=" * 80)
        print("AI Crawler Tracking + Content Store Integrated Demo")
        print("=" * 80)
        
        # Prepare URLs to crawl
        print("\n[0] Preparing URLs to crawl...")
        if not self.prepare_urls(url_limit=url_limit):
            return
        
        # Step 1: Load bot data (optional, only if paths provided)
        print("\n[1] Loading AI bot tracking data...")
        bots, bot_interactions = self.tracker.load_bot_table(self.bot_table_path)
        print(f"    Detected {len(bots)} unique AI bots")
        print(f"    Total bot interactions in table: {len(bot_interactions)}")
        
        # Step 2: Crawl each URL and store content
        print(f"\n[2] Crawling {len(self.urls_to_crawl)} URLs and storing content...")
        successful_crawls = 0
        
        for i, url in enumerate(self.urls_to_crawl, 1):
            print(f"    [{i}/{len(self.urls_to_crawl)}] Crawling {url}...", end=" ")
            try:
                doc = self.crawler.crawl(
                    url=url,
                    entity_type="owned_brand",
                    entity_name="Target Site"
                )
                
                # Try to find matching AI bots by checking if URL path appears in bot_table
                # Extract path from full URL for matching with bot_table paths
                path = urlparse(url).path or '/'
                if not path.startswith('/'):
                    path = '/' + path
                
                accessing_bots = [
                    bi['bot'] for bi in bot_interactions if bi['url'] == path
                ]
                
                # Enrich with AI bot tracking data
                doc.crawl_metadata['detected_ai_bots'] = accessing_bots
                
                self.store.add_document(doc)
                successful_crawls += 1
                print(f"✓ ({doc.metrics.get('word_count', 0)} words, {len(accessing_bots)} bots)")
            except requests.exceptions.Timeout:
                print(f"✗ Timeout - server took too long to respond")
            except requests.exceptions.ConnectionError:
                print(f"✗ Connection error - network/SSL issue")
            except requests.exceptions.HTTPError as e:
                print(f"✗ HTTP Error: {e.response.status_code}")
            except KeyboardInterrupt:
                print(f"\n✗ Crawl interrupted by user")
                break
            except Exception as e:
                print(f"✗ Error: {str(e)[:60]}")
            
            # Be polite to servers - longer delay for recovery
            import time
            time.sleep(1)
        
        print(f"\n    Successfully crawled and stored {successful_crawls} pages")
        
        # Step 3: Register bot interactions
        print("\n[3] Registering AI bot interactions...")
        interaction_count = 0
        for interaction in bot_interactions:
            path = interaction['url']
            # Normalize path
            if not path.startswith('/'):
                path = '/' + path
            
            self.tracker.add_interaction(
                bot_name=interaction['bot'],
                url=path,  # Store normalized path
                timestamp=interaction['date'],
                status_code=interaction['status']
            )
            interaction_count += 1
        
        print(f"    Registered {interaction_count} bot interactions across {len(self.tracker.url_bot_map)} unique paths")
        
        # Step 4: Generate analytics
        print("\n[4] Generating AI bot analytics...")
        summary = self.tracker.get_summary()
        self._print_analytics(summary)
        
        # Step 5: Save results
        print("\n[5] Saving results...")
        self._save_results(summary)
    
    def _print_analytics(self, summary):
        """Print analytics summary"""
        print(f"\n    Total Unique AI Bots: {summary['total_unique_bots']}")
        print(f"    Total Unique URLs Accessed by Bots: {summary['total_unique_urls_accessed']}")
        print("\n    Top AI Bots by Activity:")
        
        sorted_bots = sorted(
            summary['bots'].items(),
            key=lambda x: x[1]['interaction_count'],
            reverse=True
        )
        for bot, stats in sorted_bots[:10]:
            print(f"      - {bot}: {stats['interaction_count']} interactions, "
                  f"{stats['unique_urls']} unique URLs")
    
    def _save_results(self, summary):
        """Save analytics and content store results"""
        # Save bot analytics
        analytics_file = "ai_bot_analytics.json"
        with open(analytics_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"    ✓ Analytics saved to {analytics_file}")
        
        # Save content store
        print(f"    ✓ Content store saved to {self.store.storage_path} ({len(self.store.documents)} documents)")
        
        # Save detailed report
        report = self._generate_report()
        report_file = "ai_crawler_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"    ✓ Detailed report saved to {report_file}")
    
    def _generate_report(self):
        """Generate markdown report"""
        report = "# AI Crawler Tracking Report\n\n"
        report += f"Generated: {datetime.utcnow().isoformat()}\n\n"
        
        report += "## Content Store Summary\n"
        report += f"- Total Documents: {len(self.store.documents)}\n"
        report += f"- Average Word Count: {sum(d.metrics.get('word_count', 0) for d in self.store.documents.values()) / max(len(self.store.documents), 1):.0f}\n\n"
        
        report += "## AI Bot Interactions\n"
        for bot, interactions in sorted(self.tracker.bot_interactions.items()):
            report += f"### {bot}\n"
            report += f"- Total Interactions: {len(interactions)}\n"
            report += f"- Unique URLs: {len(set(i['url'] for i in interactions))}\n"
            report += f"- Last Interaction: {max((i['timestamp'] for i in interactions), default='N/A')}\n\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(description='AI Crawler Tracking + URL Content Store Demo')
    parser.add_argument('--website', help='Website URL to crawl and discover links from (e.g., https://example.com)')
    parser.add_argument('--csv', help='CSV file with full URLs (one per line or in "url" column)')
    parser.add_argument('--limit', type=int, default=10, help='Max pages to crawl')
    parser.add_argument('--bot-table', default='AICrawlerLogging/bot_table.csv', help='Path to bot_table.csv')
    parser.add_argument('--server-log', default='AICrawlerLogging/server_log.csv', help='Path to server_log.csv')
    
    args = parser.parse_args()
    
    if not args.website and not args.csv:
        parser.print_help()
        print("\nError: Must provide either --website or --csv")
        sys.exit(1)
    
    demo = IntegratedCrawlerDemo(
        website_url=args.website,
        csv_urls=args.csv,
        bot_table_path=args.bot_table,
        server_log_path=args.server_log
    )
    
    demo.run(url_limit=args.limit)
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
