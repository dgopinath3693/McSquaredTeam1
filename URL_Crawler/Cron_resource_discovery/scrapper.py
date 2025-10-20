#!/usr/bin/env python3
"""
Product Keyword Scraper - Integrated with GEO Content Schema
Searches for product keywords across company sites and authoritative domains,
scrapes content using ContentCrawler, and stores in ContentStore.

Setup:
1. pip install requests beautifulsoup4 pyyaml
2. Ensure schema.py, crawler.py, and store.py are in the same directory
3. Run interactively: python scraper.py
4. Run with config: python scraper.py --config config.yaml
5. Add to crontab: 0 */6 * * * /path/to/python /path/to/scraper.py --config /path/to/config.yaml
"""

import os
import json
import yaml
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse, urljoin
import time
import sys

# Import your existing schema and infrastructure
from schema import ContentDocument, EntityType
from crawler import ContentCrawler
from store import ContentStore


class ProductDiscoveryEngine:
    """Discovers product-related URLs through search and crawling"""
    
    def __init__(self, 
                 company_name: str,
                 main_domain: str,
                 keywords: List[str], 
                 additional_domains: List[str] = None):
        
        self.company_name = company_name
        self.main_domain = main_domain
        self.keywords = [k.lower() for k in keywords]
        self.base_domains = [main_domain] + (additional_domains or [])
        self.discovered_urls = {}  # URL -> entity_type mapping
        
        # Authoritative third-party domains
        self.third_party_domains = [
            'g2.com', 'capterra.com', 'trustpilot.com', 'producthunt.com',
            'gartner.com', 'crunchbase.com', 'techcrunch.com', 'forbes.com',
            'bloomberg.com', 'reuters.com', 'venturebeat.com', 'theverge.com',
            'wired.com', 'zdnet.com', 'cnet.com', 'reddit.com', 'medium.com',
            'hackernews.com', 'ycombinator.com'
        ]
        
        # Competitor domains (can be configured)
        self.competitor_domains = []
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def add_competitors(self, competitor_list: List[str]) -> None:
        """Add competitor domains for classification"""
        self.competitor_domains.extend(competitor_list)
    
    def classify_url(self, url: str) -> str:
        """Classify URL as owned_brand, competitor, or third_party"""
        domain = urlparse(url).netloc.replace('www.', '')
        
        # Check if owned brand
        if any(d in domain for d in self.base_domains):
            return EntityType.OWNED_BRAND.value
        
        # Check if competitor
        if any(d in domain for d in self.competitor_domains):
            return EntityType.COMPETITOR.value
        
        # Otherwise third party
        return EntityType.THIRD_PARTY.value
    
    def search_duckduckgo(self, query: str, num_results: int = 10) -> List[str]:
        """Search DuckDuckGo for URLs"""
        print(f"🔍 Searching: {query}")
        
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            urls = []
            for link in soup.find_all('a', class_='result__a', limit=num_results):
                href = link.get('href')
                if href and href.startswith('http'):
                    urls.append(href)
            
            return urls
        except Exception as e:
            print(f"⚠️  Search error: {e}")
            return []
    
    def is_relevant_url(self, url: str) -> bool:
        """Check if URL is relevant based on keywords and domain"""
        url_lower = url.lower()
        domain = urlparse(url).netloc.replace('www.', '')
        
        # Check if it's from base domains, competitors, or third parties
        is_base_domain = any(d in domain for d in self.base_domains)
        is_competitor = any(d in domain for d in self.competitor_domains)
        is_third_party = any(d in domain for d in self.third_party_domains)
        
        # Check if URL contains keywords or company name
        has_keywords = any(keyword in url_lower for keyword in self.keywords)
        has_company = self.company_name.lower() in url_lower
        
        return (is_base_domain or is_competitor or is_third_party) and (has_keywords or has_company)
    
    def discover_urls(self) -> Dict[str, str]:
        """
        Discover URLs using search queries with keywords
        Returns: Dict mapping URL -> entity_type
        """
        print("\n" + "="*60)
        print("🚀 Starting URL Discovery")
        print("="*60)
        
        discovered = {}
        
        # Build search queries
        search_queries = []
        
        # Company + product searches
        for keyword in self.keywords:
            search_queries.append(f"{self.company_name} {keyword}")
            search_queries.append(f"{keyword} {self.company_name}")
        
        # Review and comparison searches
        for keyword in self.keywords[:5]:  # Limit to avoid too many searches
            search_queries.append(f"{self.company_name} {keyword} review")
            search_queries.append(f"{self.company_name} {keyword} features")
            search_queries.append(f"{keyword} comparison {self.company_name}")
        
        # Direct company searches
        search_queries.extend([
            f"{self.company_name} product",
            f"{self.company_name} platform",
            f"{self.company_name} documentation"
        ])
        
        # Execute searches
        for query in search_queries[:15]:  # Limit total searches
            urls = self.search_duckduckgo(query, num_results=10)
            for url in urls:
                if self.is_relevant_url(url) and url not in discovered:
                    discovered[url] = self.classify_url(url)
            time.sleep(2)  # Rate limiting
        
        # Add direct crawl of base domains
        for domain in self.base_domains:
            base_url = f"https://{domain}" if not domain.startswith('http') else domain
            discovered[base_url] = EntityType.OWNED_BRAND.value
            
            # Common product pages
            common_pages = [
                '/products', '/features', '/pricing', '/solutions',
                '/platform', '/services', '/product', '/about',
                '/customers', '/case-studies', '/resources', '/blog',
                '/docs', '/documentation', '/faq'
            ]
            for page in common_pages:
                url = base_url + page
                discovered[url] = EntityType.OWNED_BRAND.value
        
        self.discovered_urls = discovered
        print(f"\n✅ Discovered {len(discovered)} URLs")
        print(f"   - Owned Brand: {sum(1 for t in discovered.values() if t == EntityType.OWNED_BRAND.value)}")
        print(f"   - Competitors: {sum(1 for t in discovered.values() if t == EntityType.COMPETITOR.value)}")
        print(f"   - Third Party: {sum(1 for t in discovered.values() if t == EntityType.THIRD_PARTY.value)}")
        
        return discovered


class IntegratedProductScraper:
    """
    Integrated scraper that uses ContentCrawler and ContentStore
    to maintain schema compatibility
    """
    
    def __init__(self, 
                 company_name: str,
                 main_domain: str,
                 keywords: List[str],
                 additional_domains: List[str] = None,
                 competitor_domains: List[str] = None,
                 output_dir: str = "scraper_output",
                 storage_path: str = None):
        
        self.company_name = company_name
        self.main_domain = main_domain
        self.keywords = keywords
        self.output_dir = output_dir
        
        # Initialize discovery engine
        self.discovery = ProductDiscoveryEngine(
            company_name=company_name,
            main_domain=main_domain,
            keywords=keywords,
            additional_domains=additional_domains
        )
        
        if competitor_domains:
            self.discovery.add_competitors(competitor_domains)
        
        # Initialize crawler and store
        self.crawler = ContentCrawler(crawler_id=f"product-scraper-{company_name.lower().replace(' ', '-')}")
        
        if not storage_path:
            storage_path = os.path.join(output_dir, f"{company_name.lower().replace(' ', '_')}_content_store.json")
        
        self.store = ContentStore(storage_path=storage_path)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Stats
        self.stats = {
            'total_discovered': 0,
            'successful_crawls': 0,
            'failed_crawls': 0,
            'by_entity_type': {},
            'by_content_type': {}
        }
    
    def run(self):
        """Execute complete scraping workflow"""
        start_time = time.time()
        
        print("\n" + "🤖 " + "="*58)
        print(f"   INTEGRATED PRODUCT SCRAPER - {self.company_name.upper()}")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Company: {self.company_name}")
        print(f"Main Domain: {self.main_domain}")
        print(f"Keywords: {', '.join(self.keywords)}")
        
        # Phase 1: Discovery
        discovered_urls = self.discovery.discover_urls()
        self.stats['total_discovered'] = len(discovered_urls)
        
        # Phase 2: Crawl and store
        print("\n" + "="*60)
        print("📥 Starting Content Crawling")
        print("="*60)
        
        for i, (url, entity_type) in enumerate(discovered_urls.items(), 1):
            print(f"\n[{i}/{len(discovered_urls)}] Crawling: {url}")
            
            try:
                # Use ContentCrawler to extract structured content
                doc = self.crawler.crawl(
                    url=url,
                    entity_type=entity_type,
                    entity_name=self._get_entity_name(url, entity_type)
                )
                
                # Add keyword relevance analysis
                doc.topics = self._extract_topics(doc)
                doc.entities_mentioned = self._extract_entity_mentions(doc)
                
                # Store in ContentStore
                self.store.add_document(doc)
                
                # Update stats
                self.stats['successful_crawls'] += 1
                self.stats['by_entity_type'][entity_type] = \
                    self.stats['by_entity_type'].get(entity_type, 0) + 1
                self.stats['by_content_type'][doc.content_type] = \
                    self.stats['by_content_type'].get(doc.content_type, 0) + 1
                
                print(f"✅ Stored as {doc.content_type} ({doc.metrics['word_count']} words)")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                self.stats['failed_crawls'] += 1
            
            time.sleep(1)  # Rate limiting
        
        # Phase 3: Generate reports
        self.generate_summary()
        self.export_results()
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  Total time: {elapsed:.2f} seconds")
        print(f"📊 Content store: {self.store.storage_path}")
        print("="*60 + "\n")
    
    def _get_entity_name(self, url: str, entity_type: str) -> str:
        """Extract entity name from URL"""
        domain = urlparse(url).netloc.replace('www.', '')
        
        if entity_type == EntityType.OWNED_BRAND.value:
            return self.company_name
        else:
            # Use domain as entity name for competitors/third parties
            return domain.split('.')[0].title()
    
    def _extract_topics(self, doc: ContentDocument) -> List[str]:
        """Extract topics based on keyword presence"""
        topics = []
        text_lower = doc.clean_text.lower()
        
        for keyword in self.keywords:
            if keyword in text_lower:
                topics.append(keyword)
        
        return topics
    
    def _extract_entity_mentions(self, doc: ContentDocument) -> List[str]:
        """Extract company/competitor mentions"""
        mentions = []
        text_lower = doc.clean_text.lower()
        
        # Check for company mention
        if self.company_name.lower() in text_lower:
            mentions.append(self.company_name)
        
        # Check for competitor mentions
        for competitor in self.discovery.competitor_domains:
            competitor_name = competitor.split('.')[0].title()
            if competitor_name.lower() in text_lower:
                mentions.append(competitor_name)
        
        return mentions
    
    def generate_summary(self):
        """Generate and print summary statistics"""
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        
        print(f"\n📍 URLs Discovered: {self.stats['total_discovered']}")
        print(f"✅ Successful Crawls: {self.stats['successful_crawls']}")
        print(f"❌ Failed Crawls: {self.stats['failed_crawls']}")
        
        print(f"\n🏢 By Entity Type:")
        for entity_type, count in self.stats['by_entity_type'].items():
            print(f"   {entity_type}: {count} documents")
        
        print(f"\n📄 By Content Type:")
        for content_type, count in self.stats['by_content_type'].items():
            print(f"   {content_type}: {count} documents")
        
        # Analysis from ContentStore
        print(f"\n🔍 Keyword Analysis:")
        all_docs = list(self.store.documents.values())
        keyword_counts = {kw: 0 for kw in self.keywords}
        
        for doc in all_docs:
            for topic in doc.topics:
                if topic in keyword_counts:
                    keyword_counts[topic] += 1
        
        for kw, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {kw}: mentioned in {count} documents")
    
    def export_results(self):
        """Export results in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_slug = self.company_name.lower().replace(' ', '_')
        
        # Export all documents for analysis
        analysis_data = self.store.export_for_analysis()
        
        analysis_path = os.path.join(
            self.output_dir, 
            f"{company_slug}_analysis_{timestamp}.json"
        )
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        # Export URL list with classifications
        urls_path = os.path.join(
            self.output_dir,
            f"{company_slug}_urls_{timestamp}.txt"
        )
        with open(urls_path, 'w') as f:
            f.write(f"Discovered URLs for {self.company_name}\n")
            f.write("="*60 + "\n\n")
            
            for entity_type in [EntityType.OWNED_BRAND.value, 
                               EntityType.COMPETITOR.value, 
                               EntityType.THIRD_PARTY.value]:
                docs = self.store.get_by_type(entity_type)
                if docs:
                    f.write(f"\n{entity_type.upper()} ({len(docs)} URLs):\n")
                    f.write("-"*60 + "\n")
                    for doc in docs:
                        f.write(f"{doc.url}\n")
        
        print(f"\n✅ Exports saved:")
        print(f"   📄 Analysis JSON: {analysis_path}")
        print(f"   📋 URL List: {urls_path}")
        print(f"   💾 Content Store: {self.store.storage_path}")


def interactive_mode():
    """Interactive mode to gather user input"""
    print("\n" + "="*60)
    print("🎯 INTEGRATED PRODUCT SCRAPER - SETUP")
    print("="*60 + "\n")
    
    company_name = input("Enter company name: ").strip()
    if not company_name:
        print("❌ Company name is required!")
        sys.exit(1)
    
    main_domain = input("Enter main company domain (e.g., company.com): ").strip()
    if not main_domain:
        print("❌ Main domain is required!")
        sys.exit(1)
    
    print("\nEnter product/service keywords (comma-separated):")
    keywords_input = input("Keywords: ").strip()
    if not keywords_input:
        print("❌ At least one keyword is required!")
        sys.exit(1)
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    print("\nEnter additional domains to monitor (comma-separated, optional):")
    additional_input = input("Additional domains: ").strip()
    additional_domains = [d.strip() for d in additional_input.split(',') if d.strip()] if additional_input else []
    
    print("\nEnter competitor domains (comma-separated, optional):")
    competitor_input = input("Competitor domains: ").strip()
    competitor_domains = [d.strip() for d in competitor_input.split(',') if d.strip()] if competitor_input else []
    
    output_dir = input("\nOutput directory (default: scraper_output): ").strip() or "scraper_output"
    
    save_config = input("\nSave this configuration? (y/n): ").strip().lower() == 'y'
    
    config = {
        'company_name': company_name,
        'main_domain': main_domain,
        'keywords': keywords,
        'additional_domains': additional_domains,
        'competitor_domains': competitor_domains,
        'output_dir': output_dir
    }
    
    if save_config:
        config_path = input("Config filename (default: config.yaml): ").strip() or "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"✅ Configuration saved to {config_path}")
    
    return config


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✅ Loaded configuration from {config_path}")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Integrated Product Keyword Scraper')
    parser.add_argument('--config', type=str, help='Path to YAML configuration file')
    parser.add_argument('--company', type=str, help='Company name')
    parser.add_argument('--domain', type=str, help='Main company domain')
    parser.add_argument('--keywords', type=str, help='Comma-separated keywords')
    parser.add_argument('--additional-domains', type=str, help='Comma-separated additional domains')
    parser.add_argument('--competitor-domains', type=str, help='Comma-separated competitor domains')
    parser.add_argument('--output', type=str, default='scraper_output', help='Output directory')
    
    args = parser.parse_args()
    
    # Determine configuration source
    if args.config:
        config = load_config(args.config)
    elif args.company and args.domain and args.keywords:
        config = {
            'company_name': args.company,
            'main_domain': args.domain,
            'keywords': [k.strip() for k in args.keywords.split(',')],
            'additional_domains': [d.strip() for d in args.additional_domains.split(',')] if args.additional_domains else [],
            'competitor_domains': [d.strip() for d in args.competitor_domains.split(',')] if args.competitor_domains else [],
            'output_dir': args.output
        }
    else:
        config = interactive_mode()
    
    # Initialize and run integrated scraper
    scraper = IntegratedProductScraper(
        company_name=config['company_name'],
        main_domain=config['main_domain'],
        keywords=config['keywords'],
        additional_domains=config.get('additional_domains', []),
        competitor_domains=config.get('competitor_domains', []),
        output_dir=config.get('output_dir', 'scraper_output')
    )
    
    scraper.run()


if __name__ == "__main__":
    main()