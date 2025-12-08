"""
Domain Score Calculator
Calculates brand/domain visibility scores based on crawler, extraction, and gap analysis outputs.
"""
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class DomainScoreCalculator:
    """
    Calculates domain visibility scores by aggregating data from:
    - Crawler outputs (ai_crawler_store.json)
    - Gap analysis results (gap_analysis_results.json)
    - Bot analytics (ai_bot_analytics.json)
    - Extraction outputs (CSV files)
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the calculator with base path to data files.
        
        Args:
            base_path: Base directory path. If None, uses parent directory of FastAPIApp.
        """
        if base_path is None:
            # Default to parent directory of FastAPIApp
            current_dir = Path(__file__).parent
            self.base_path = current_dir.parent
        else:
            self.base_path = Path(base_path)
        
        self.crawler_store_path = self.base_path / "ai_crawler_store.json"
        self.gap_analysis_path = self.base_path / "gap_analysis_results.json"
        self.bot_analytics_path = self.base_path / "ai_bot_analytics.json"
        self.extraction_csv_path = self.base_path / "AiExtractionAgent" / "ai_responses_cleaned.csv"
    
    def load_crawler_data(self) -> Dict[str, Any]:
        """Load crawler store data."""
        try:
            if self.crawler_store_path.exists():
                with open(self.crawler_store_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading crawler data: {e}")
            return {}
    
    def load_gap_analysis(self) -> Dict[str, Any]:
        """Load gap analysis results."""
        try:
            if self.gap_analysis_path.exists():
                with open(self.gap_analysis_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading gap analysis: {e}")
            return {}
    
    def load_bot_analytics(self) -> Dict[str, Any]:
        """Load bot analytics data."""
        try:
            if self.bot_analytics_path.exists():
                with open(self.bot_analytics_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading bot analytics: {e}")
            return {}
    
    def load_extraction_data(self) -> List[Dict[str, Any]]:
        """Load extraction CSV data."""
        try:
            import pandas as pd
            if self.extraction_csv_path.exists():
                df = pd.read_csv(self.extraction_csv_path)
                return df.to_dict('records')
            return []
        except Exception as e:
            print(f"Error loading extraction data: {e}")
            return []
    
    def calculate_crawler_score(self, crawler_data: Dict[str, Any], brand: str) -> float:
        """
        Calculate score based on crawler data.
        Factors: number of URLs, content quality, structured data presence.
        """
        if not crawler_data:
            return 0.0
        
        brand_docs = [
            doc for doc in crawler_data.values()
            if doc.get('entity_name', '').lower() == brand.lower()
        ]
        
        if not brand_docs:
            return 0.0
        
        # Score components
        url_count_score = min(len(brand_docs) / 50.0, 1.0) * 0.3  # Max 30 points for URL count
        
        # Content quality score (word count, headings, structured data)
        total_word_count = sum(doc.get('metrics', {}).get('word_count', 0) for doc in brand_docs)
        avg_word_count = total_word_count / len(brand_docs) if brand_docs else 0
        content_quality_score = min(avg_word_count / 1000.0, 1.0) * 0.2  # Max 20 points
        
        # Structured data score
        docs_with_schema = sum(
            1 for doc in brand_docs
            if doc.get('metrics', {}).get('has_schema', False) or
               doc.get('structured_data', {}).get('schema_type')
        )
        schema_score = (docs_with_schema / len(brand_docs)) * 0.2 if brand_docs else 0  # Max 20 points
        
        # FAQ presence score
        docs_with_faq = sum(
            1 for doc in brand_docs
            if doc.get('metrics', {}).get('has_faq', False) or
               (doc.get('structured_data', {}).get('faq_items') and 
                len(doc.get('structured_data', {}).get('faq_items', [])) > 0)
        )
        faq_score = (docs_with_faq / len(brand_docs)) * 0.15 if brand_docs else 0  # Max 15 points
        
        # Response code score (successful crawls)
        successful_crawls = sum(
            1 for doc in brand_docs
            if doc.get('crawl_metadata', {}).get('response_code') == 200
        )
        crawl_success_score = (successful_crawls / len(brand_docs)) * 0.15 if brand_docs else 0  # Max 15 points
        
        total_score = (url_count_score + content_quality_score + schema_score + 
                      faq_score + crawl_success_score) * 100
        
        return round(total_score, 2)
    
    def calculate_gap_analysis_score(self, gap_analysis: Dict[str, Any], brand: str) -> float:
        """
        Calculate score based on gap analysis.
        Lower gap scores = higher visibility score.
        """
        if not gap_analysis:
            return 50.0  # Default neutral score
        
        owned_entity = gap_analysis.get('owned_entity', '')
        if owned_entity.lower() != brand.lower():
            return 50.0  # Not for this brand
        
        top_gaps = gap_analysis.get('top_gaps', [])
        if not top_gaps:
            return 100.0  # No gaps = perfect score
        
        # Calculate average gap score
        gap_scores = [gap.get('gap_score', 0) for gap in top_gaps]
        avg_gap_score = sum(gap_scores) / len(gap_scores) if gap_scores else 0
        
        # Convert gap score to visibility score (inverse relationship)
        # Higher gap = lower visibility
        # Normalize: gap scores typically 0-0.3, so we scale accordingly
        visibility_score = max(0, 100 - (avg_gap_score * 200))
        
        # Penalty for high priority gaps
        high_priority_gaps = sum(1 for gap in top_gaps if gap.get('priority') == 'High')
        priority_penalty = min(high_priority_gaps * 5, 30)  # Max 30 point penalty
        
        final_score = max(0, visibility_score - priority_penalty)
        return round(final_score, 2)
    
    def calculate_bot_analytics_score(self, bot_analytics: Dict[str, Any]) -> float:
        """
        Calculate score based on bot analytics.
        More bot interactions = better visibility.
        """
        if not bot_analytics:
            return 0.0
        
        total_interactions = sum(
            bot.get('interaction_count', 0)
            for bot in bot_analytics.get('bots', {}).values()
        )
        
        # Normalize: 1000+ interactions = full score
        interaction_score = min(total_interactions / 1000.0, 1.0) * 0.4  # Max 40 points
        
        unique_urls = bot_analytics.get('total_unique_urls_accessed', 0)
        url_diversity_score = min(unique_urls / 100.0, 1.0) * 0.3  # Max 30 points
        
        # Success rate (200 status codes)
        total_200s = 0
        total_requests = 0
        for bot_data in bot_analytics.get('bots', {}).values():
            status_codes = bot_data.get('status_codes', {})
            total_200s += status_codes.get('200', 0)
            total_requests += bot_data.get('interaction_count', 0)
        
        success_rate = (total_200s / total_requests) if total_requests > 0 else 0
        success_score = success_rate * 0.3  # Max 30 points
        
        total_score = (interaction_score + url_diversity_score + success_score) * 100
        return round(total_score, 2)
    
    def calculate_extraction_score(self, extraction_data: List[Dict[str, Any]]) -> float:
        """
        Calculate score based on extraction data.
        More successful extractions = better visibility.
        """
        if not extraction_data:
            return 0.0
        
        total_extractions = len(extraction_data)
        successful_extractions = sum(
            1 for record in extraction_data
            if record.get('status') == 'success'
        )
        
        success_rate = (successful_extractions / total_extractions) if total_extractions > 0 else 0
        
        # Average answer length (longer = more content)
        answer_lengths = [
            record.get('answer_length', 0) or 0
            for record in extraction_data
            if record.get('status') == 'success'
        ]
        avg_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
        length_score = min(avg_length / 500.0, 1.0)  # Normalize to 500 chars
        
        # Combined score
        total_score = (success_rate * 0.7 + length_score * 0.3) * 100
        return round(total_score, 2)
    
    def calculate_domain_score(self, brand: str) -> Dict[str, Any]:
        """
        Calculate overall domain visibility score for a brand.
        
        Args:
            brand: Brand name to calculate score for
            
        Returns:
            Dictionary with score breakdown and metadata
        """
        # Load all data sources
        crawler_data = self.load_crawler_data()
        gap_analysis = self.load_gap_analysis()
        bot_analytics = self.load_bot_analytics()
        extraction_data = self.load_extraction_data()
        
        # Calculate component scores
        crawler_score = self.calculate_crawler_score(crawler_data, brand)
        gap_score = self.calculate_gap_analysis_score(gap_analysis, brand)
        bot_score = self.calculate_bot_analytics_score(bot_analytics)
        extraction_score = self.calculate_extraction_score(extraction_data)
        
        # Weighted overall score
        # Crawler: 30%, Gap Analysis: 30%, Bot Analytics: 25%, Extraction: 15%
        overall_score = (
            crawler_score * 0.30 +
            gap_score * 0.30 +
            bot_score * 0.25 +
            extraction_score * 0.15
        )
        
        return {
            'brand': brand,
            'overall_score': round(overall_score, 2),
            'score_breakdown': {
                'crawler_score': crawler_score,
                'gap_analysis_score': gap_score,
                'bot_analytics_score': bot_score,
                'extraction_score': extraction_score
            },
            'weights': {
                'crawler': 0.30,
                'gap_analysis': 0.30,
                'bot_analytics': 0.25,
                'extraction': 0.15
            },
            'metadata': {
                'crawler_docs_count': len([d for d in crawler_data.values() 
                                          if d.get('entity_name', '').lower() == brand.lower()]) if crawler_data else 0,
                'total_gaps': gap_analysis.get('total_gaps_identified', 0) if gap_analysis else 0,
                'bot_interactions': sum(b.get('interaction_count', 0) 
                                       for b in bot_analytics.get('bots', {}).values()) if bot_analytics else 0,
                'extraction_count': len(extraction_data)
            }
        }

