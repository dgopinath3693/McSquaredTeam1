"""
Competitive Gap Analysis Demo
==============================

Enhanced AI Crawler + Content Store with Competitive Gap Analysis

This demo extends the basic crawler to support competitive analysis:
1. Crawl and store content for YOUR entity (owned_brand)
2. Crawl and store content for COMPETITOR entities
3. Perform gap analysis to identify content opportunities
4. Generate report showing keyword gaps and coverage analysis

Features:
- Multi-entity crawling (owned brand + competitors)
- Entity-classified content storage
- TF-IDF based gap analysis
- Coverage comparison
- Keyword opportunity identification
- AI bot tracking per entity

Run:
  python3 URL_Crawler/demo_competitive_gap_analysis.py \
    --entity "Nike" --entity-csv nike_urls.csv \
    --competitor "Adidas" --competitor-csv adidas_urls.csv \
    --limit 5
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Add URL_Crawler to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from crawler import ContentCrawler
from store import ContentStore
from schema import ContentDocument, ContentMetrics, CrawlMetadata


class CompetitiveGapAnalyzer:
    """Performs competitive gap analysis on crawled content"""
    
    def __init__(self):
        self.entity_documents = {}  # entity_name -> [ContentDocument]
    
    def add_documents(self, entity_name, documents):
        """Add documents for an entity"""
        self.entity_documents[entity_name] = documents
    
    def extract_text_per_entity(self):
        """Extract clean text per entity"""
        entity_texts = {}
        for entity_name, docs in self.entity_documents.items():
            combined_text = " ".join([
                doc.clean_text or "" for doc in docs
            ])
            entity_texts[entity_name] = combined_text
        return entity_texts
    
    def perform_gap_analysis(self, owned_entity, competitor_entities, top_gaps=15):
        """
        Analyze content gaps between owned brand and competitors.
        
        Returns gaps where competitors have content but owned brand is weak.
        """
        entity_texts = self.extract_text_per_entity()
        
        if owned_entity not in entity_texts:
            return {"error": f"Owned entity '{owned_entity}' not found"}
        
        own_text = entity_texts[owned_entity]
        
        # Vectorize owned brand content
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=2000,
            ngram_range=(1, 2)
        )
        
        # Include all texts for fitting
        all_texts = [own_text] + [
            entity_texts.get(comp, "") for comp in competitor_entities
        ]
        
        try:
            tfidf_matrix = vectorizer.fit_transform(all_texts)
        except Exception as e:
            return {"error": f"Gap analysis failed: {str(e)}"}
        
        own_vector = tfidf_matrix[0]
        feature_names = np.array(vectorizer.get_feature_names_out())
        
        gaps = []
        
        # For each competitor, find unique strong terms
        for i, competitor in enumerate(competitor_entities):
            if competitor not in entity_texts:
                continue
            
            comp_vector = tfidf_matrix[i + 1]
            
            # Find terms where competitor is strong but owned is weak
            own_scores = own_vector.toarray()[0]
            comp_scores = comp_vector.toarray()[0]
            
            # Gap score: competitor strong, owned weak
            gap_scores = comp_scores - own_scores
            
            # Get top gap terms
            top_indices = np.argsort(gap_scores)[-top_gaps:]
            
            for idx in reversed(top_indices):
                if gap_scores[idx] > 0:
                    gaps.append({
                        "term": feature_names[idx],
                        "competitor": competitor,
                        "competitor_strength": float(comp_scores[idx]),
                        "owned_strength": float(own_scores[idx]),
                        "gap_score": float(gap_scores[idx]),
                        "priority": "High" if gap_scores[idx] > 0.1 else "Medium"
                    })
        
        # Sort by gap score
        gaps = sorted(gaps, key=lambda x: x['gap_score'], reverse=True)[:top_gaps]
        
        return {
            "owned_entity": owned_entity,
            "competitors": competitor_entities,
            "total_gaps_identified": len(gaps),
            "top_gaps": gaps
        }
    
    def generate_coverage_comparison(self):
        """Generate coverage statistics per entity"""
        coverage = {}
        for entity_name, docs in self.entity_documents.items():
            total_words = sum(d.metrics.get('word_count', 0) for d in docs)
            total_images = sum(d.metrics.get('image_count', 0) for d in docs)
            total_links = sum(d.metrics.get('link_count', 0) for d in docs)
            
            coverage[entity_name] = {
                "pages_crawled": len(docs),
                "total_words": total_words,
                "avg_words_per_page": total_words // max(len(docs), 1),
                "total_images": total_images,
                "total_links": total_links,
                "content_types": Counter([d.content_type for d in docs])
            }
        
        return coverage


class CompetitiveGapDemo:
    """Main orchestrator for competitive gap analysis demo"""
    
    def __init__(self, bot_table_path=None, server_log_path=None):
        self.crawler = ContentCrawler(crawler_id="gap-analysis-v1")
        self.analyzer = CompetitiveGapAnalyzer()
        self.bot_table_path = bot_table_path or 'AICrawlerLogging/bot_table.csv'
        self.server_log_path = server_log_path or 'AICrawlerLogging/server_log.csv'
        self.all_documents = {}  # entity_name -> [docs]
    
    def load_urls_from_csv(self, filepath):
        """Load URLs from CSV"""
        urls = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample = f.readline()
                f.seek(0)
                
                if 'url' in sample.lower() or 'http' not in sample:
                    reader = csv.DictReader(f)
                    for row in reader:
                        url = row.get('url') or row.get('URL') or row.get('Url')
                        if url and url.startswith('http'):
                            urls.append(url.strip())
                else:
                    for line in f:
                        line = line.strip()
                        if line.startswith('http'):
                            urls.append(line)
        except FileNotFoundError:
            print(f"Error: CSV file {filepath} not found")
        
        return urls
    
    def crawl_entity(self, entity_name, entity_type, csv_path, url_limit=10):
        """Crawl URLs for a specific entity"""
        print(f"\n[Entity: {entity_name}] Loading URLs from {csv_path}...")
        urls = self.load_urls_from_csv(csv_path)[:url_limit]
        print(f"  Prepared {len(urls)} URLs to crawl")
        
        documents = []
        successful = 0
        
        for i, url in enumerate(urls, 1):
            print(f"  [{i}/{len(urls)}] Crawling {url}...", end=" ")
            try:
                doc = self.crawler.crawl(
                    url=url,
                    entity_type=entity_type,
                    entity_name=entity_name
                )
                documents.append(doc)
                successful += 1
                print(f"✓ ({doc.metrics.get('word_count', 0)} words)")
            except Exception as e:
                print(f"✗ {str(e)[:40]}")
            
            import time
            time.sleep(1)
        
        print(f"  Successfully crawled {successful}/{len(urls)} pages")
        self.all_documents[entity_name] = documents
        self.analyzer.add_documents(entity_name, documents)
        
        return documents
    
    def run(self, entity_name, entity_csv, competitors, competitor_csvs, url_limit=5):
        """Execute full competitive gap analysis"""
        print("=" * 80)
        print("Competitive Gap Analysis Demo")
        print("=" * 80)
        
        # Crawl owned entity
        print(f"\n>>> CRAWLING OWNED ENTITY: {entity_name}")
        self.crawl_entity(entity_name, "owned_brand", entity_csv, url_limit)
        
        # Crawl competitors
        print(f"\n>>> CRAWLING COMPETITORS")
        for competitor, csv_path in zip(competitors, competitor_csvs):
            self.crawl_entity(competitor, "competitor", csv_path, url_limit)
        
        # Perform gap analysis
        print(f"\n>>> PERFORMING GAP ANALYSIS")
        gap_results = self.analyzer.perform_gap_analysis(
            owned_entity=entity_name,
            competitor_entities=competitors,
            top_gaps=15
        )
        
        # Generate coverage comparison
        print(f"\n>>> GENERATING COVERAGE COMPARISON")
        coverage = self.analyzer.generate_coverage_comparison()
        
        # Print results
        self._print_results(gap_results, coverage)
        
        # Save results
        self._save_results(gap_results, coverage)
    
    def _print_results(self, gap_results, coverage):
        """Print analysis results"""
        print("\n" + "=" * 80)
        print("COVERAGE COMPARISON")
        print("=" * 80)
        
        for entity, stats in coverage.items():
            print(f"\n{entity}:")
            print(f"  Pages Crawled: {stats['pages_crawled']}")
            print(f"  Total Words: {stats['total_words']:,}")
            print(f"  Avg Words/Page: {stats['avg_words_per_page']:,}")
            print(f"  Total Images: {stats['total_images']}")
            print(f"  Total Links: {stats['total_links']}")
        
        print("\n" + "=" * 80)
        print("CONTENT GAPS IDENTIFIED")
        print("=" * 80)
        
        if "error" in gap_results:
            print(f"Error: {gap_results['error']}")
            return
        
        print(f"\nOwned Entity: {gap_results['owned_entity']}")
        print(f"Competitors: {', '.join(gap_results['competitors'])}")
        print(f"Total Gaps: {gap_results['total_gaps_identified']}\n")
        
        print("TOP CONTENT GAPS (opportunities to cover):")
        for i, gap in enumerate(gap_results['top_gaps'][:10], 1):
            print(f"\n{i}. {gap['term'].upper()}")
            print(f"   Priority: {gap['priority']}")
            print(f"   Competitor ({gap['competitor']}): {gap['competitor_strength']:.3f}")
            print(f"   {gap_results['owned_entity']}: {gap['owned_strength']:.3f}")
            print(f"   Gap Score: {gap['gap_score']:.3f}")
    
    def _save_results(self, gap_results, coverage):
        """Save analysis results to files"""
        # Save gap analysis
        with open("gap_analysis_results.json", "w") as f:
            # Convert numpy types to Python types
            clean_gaps = []
            for gap in gap_results.get('top_gaps', []):
                clean_gaps.append({
                    "term": str(gap['term']),
                    "competitor": gap['competitor'],
                    "competitor_strength": float(gap['competitor_strength']),
                    "owned_strength": float(gap['owned_strength']),
                    "gap_score": float(gap['gap_score']),
                    "priority": gap['priority']
                })
            
            clean_results = {
                "owned_entity": gap_results.get('owned_entity'),
                "competitors": gap_results.get('competitors', []),
                "total_gaps_identified": gap_results.get('total_gaps_identified', 0),
                "top_gaps": clean_gaps
            }
            json.dump(clean_results, f, indent=2)
        
        print(f"\n✓ Gap analysis saved to gap_analysis_results.json")
        
        # Save coverage comparison
        with open("coverage_comparison.json", "w") as f:
            json.dump(coverage, f, indent=2, default=str)
        
        print(f"✓ Coverage comparison saved to coverage_comparison.json")
        
        # Generate markdown report
        report = self._generate_report(gap_results, coverage)
        with open("competitive_gap_report.md", "w") as f:
            f.write(report)
        
        print(f"✓ Detailed report saved to competitive_gap_report.md")
    
    def _generate_report(self, gap_results, coverage):
        """Generate markdown report"""
        report = "# Competitive Gap Analysis Report\n\n"
        report += f"**Generated**: {datetime.utcnow().isoformat()}\n\n"
        
        report += "## Executive Summary\n\n"
        report += f"**Owned Entity**: {gap_results.get('owned_entity')}\n"
        report += f"**Competitors Analyzed**: {len(gap_results.get('competitors', []))}\n"
        report += f"**Content Gaps Identified**: {gap_results.get('total_gaps_identified', 0)}\n\n"
        
        report += "## Coverage Metrics\n\n"
        for entity, stats in coverage.items():
            report += f"### {entity}\n"
            report += f"- **Pages Crawled**: {stats['pages_crawled']}\n"
            report += f"- **Total Content Words**: {stats['total_words']:,}\n"
            report += f"- **Avg Words per Page**: {stats['avg_words_per_page']:,}\n"
            report += f"- **Images**: {stats['total_images']}\n"
            report += f"- **Links**: {stats['total_links']}\n\n"
        
        report += "## Top Content Gaps\n\n"
        report += "| # | Term | Competitor | Gap Priority | Your Coverage | Their Coverage |\n"
        report += "|---|------|-----------|--------|---|---|\n"
        
        for i, gap in enumerate(gap_results.get('top_gaps', [])[:15], 1):
            report += f"| {i} | **{gap['term']}** | {gap['competitor']} | {gap['priority']} | {gap['owned_strength']:.2%} | {gap['competitor_strength']:.2%} |\n"
        
        report += "\n## Recommendations\n\n"
        report += "1. **High Priority Gaps**: Create content addressing these terms to match competitor coverage\n"
        report += "2. **Medium Priority Gaps**: Enhance existing content with these topics\n"
        report += "3. **Strategic Focus**: Prioritize gaps that align with business objectives\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Competitive Gap Analysis Demo')
    parser.add_argument('--entity', required=True, help='Your entity name (e.g., Nike)')
    parser.add_argument('--entity-csv', required=True, help='CSV file with your entity URLs')
    parser.add_argument('--competitor', action='append', dest='competitors', help='Competitor name (can be used multiple times)')
    parser.add_argument('--competitor-csv', action='append', dest='competitor_csvs', help='Competitor CSV files (can be used multiple times)')
    parser.add_argument('--limit', type=int, default=5, help='Max pages per entity')
    parser.add_argument('--bot-table', default='AICrawlerLogging/bot_table.csv', help='Path to bot_table.csv')
    parser.add_argument('--server-log', default='AICrawlerLogging/server_log.csv', help='Path to server_log.csv')
    
    args = parser.parse_args()
    
    if not args.competitors or not args.competitor_csvs:
        parser.print_help()
        print("\nError: Must provide at least one --competitor and --competitor-csv pair")
        sys.exit(1)
    
    if len(args.competitors) != len(args.competitor_csvs):
        print("Error: Number of --competitor and --competitor-csv must match")
        sys.exit(1)
    
    demo = CompetitiveGapDemo(
        bot_table_path=args.bot_table,
        server_log_path=args.server_log
    )
    
    demo.run(
        entity_name=args.entity,
        entity_csv=args.entity_csv,
        competitors=args.competitors,
        competitor_csvs=args.competitor_csvs,
        url_limit=args.limit
    )
    
    print("\n" + "=" * 80)
    print("Competitive Gap Analysis Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
