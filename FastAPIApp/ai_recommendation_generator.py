"""
AI-Powered Recommendation Generator
Uses Google Gemini to generate detailed explanations and recommendations for domain scores.
"""
import os
from typing import Dict, Any, Optional, Tuple


class AIRecommendationGenerator:
    """
    Generates AI-powered recommendations using Google Gemini API.
    Provides explanations for domain scores and actionable improvement suggestions.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the recommendation generator.
        
        Args:
            api_key: Google Gemini API key. If None, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable.")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except ImportError:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini: {e}")
    
    def generate_recommendations(self, score_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate AI-powered recommendations based on domain score data.
        
        Args:
            score_data: Dictionary containing score breakdown and metadata from DomainScoreCalculator
            
        Returns:
            Dictionary with 'explanation' and 'recommendations' keys
        """
        brand = score_data.get('brand', 'Unknown')
        overall_score = score_data.get('overall_score', 0)
        breakdown = score_data.get('score_breakdown', {})
        metadata = score_data.get('metadata', {})
        
        # Build prompt for Gemini
        prompt = f"""You are a digital marketing and SEO expert analyzing a brand's online visibility score.

Brand: {brand}
Overall Visibility Score: {overall_score}/100

Score Breakdown:
- Crawler Score: {breakdown.get('crawler_score', 0)}/100 (measures content coverage, quality, and structured data)
- Gap Analysis Score: {breakdown.get('gap_analysis_score', 0)}/100 (measures competitive content gaps)
- Bot Analytics Score: {breakdown.get('bot_analytics_score', 0)}/100 (measures search engine bot interactions)
- Extraction Score: {breakdown.get('extraction_score', 0)}/100 (measures AI model extraction success)

Metadata:
- Crawler Documents: {metadata.get('crawler_docs_count', 0)}
- Total Content Gaps Identified: {metadata.get('total_gaps', 0)}
- Bot Interactions: {metadata.get('bot_interactions', 0)}
- Extraction Records: {metadata.get('extraction_count', 0)}

Please provide:
1. A detailed explanation (2-3 paragraphs) of why this brand received this score. Analyze each component and explain what factors contributed to the score.

2. Concrete, actionable recommendations (5-7 specific actions) to improve the score. Focus on:
   - Content strategy improvements
   - Technical SEO enhancements
   - Structured data optimization
   - Competitive gap filling
   - Bot accessibility improvements

Format your response as:
EXPLANATION:
[Your explanation here]

RECOMMENDATIONS:
1. [First recommendation]
2. [Second recommendation]
..."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Parse response into explanation and recommendations
            explanation, recommendations = self._parse_response(response_text)
            
            return {
                'explanation': explanation,
                'recommendations': recommendations,
                'raw_response': response_text
            }
        except Exception as e:
            # Fallback if API call fails
            return {
                'explanation': f"Unable to generate AI recommendations: {str(e)}",
                'recommendations': self._generate_fallback_recommendations(score_data),
                'raw_response': None,
                'error': str(e)
            }
    
    def _parse_response(self, response_text: str) -> Tuple[str, str]:
        """Parse Gemini response into explanation and recommendations."""
        explanation = ""
        recommendations = ""
        
        # Try to split by section headers
        if "EXPLANATION:" in response_text:
            parts = response_text.split("EXPLANATION:", 1)
            if len(parts) > 1:
                rest = parts[1]
                if "RECOMMENDATIONS:" in rest:
                    explanation, recommendations = rest.split("RECOMMENDATIONS:", 1)
                    explanation = explanation.strip()
                    recommendations = recommendations.strip()
                else:
                    explanation = rest.strip()
        elif "RECOMMENDATIONS:" in response_text:
            parts = response_text.split("RECOMMENDATIONS:", 1)
            if len(parts) > 1:
                recommendations = parts[1].strip()
                explanation = parts[0].strip()
        else:
            # If no clear structure, use first half as explanation, second as recommendations
            lines = response_text.split('\n')
            mid_point = len(lines) // 2
            explanation = '\n'.join(lines[:mid_point]).strip()
            recommendations = '\n'.join(lines[mid_point:]).strip()
        
        return explanation or "No explanation provided.", recommendations or "No recommendations provided."
    
    def _generate_fallback_recommendations(self, score_data: Dict[str, Any]) -> str:
        """Generate basic recommendations if AI fails."""
        breakdown = score_data.get('score_breakdown', {})
        recommendations = []
        
        if breakdown.get('crawler_score', 0) < 50:
            recommendations.append("Improve content coverage by crawling more URLs and ensuring high-quality content.")
            recommendations.append("Add structured data (Schema.org) to improve search engine understanding.")
        
        if breakdown.get('gap_analysis_score', 0) < 50:
            recommendations.append("Address competitive content gaps by creating content for high-priority keywords.")
            recommendations.append("Analyze competitor content strategies and fill identified gaps.")
        
        if breakdown.get('bot_analytics_score', 0) < 50:
            recommendations.append("Improve bot accessibility by fixing crawl errors and ensuring proper robots.txt configuration.")
            recommendations.append("Optimize server response times and reduce 404/500 errors.")
        
        if breakdown.get('extraction_score', 0) < 50:
            recommendations.append("Improve content quality to ensure AI models can successfully extract information.")
            recommendations.append("Ensure content is well-structured and contains clear, extractable information.")
        
        if not recommendations:
            recommendations.append("Maintain current content strategy and monitor score trends.")
        
        return "\n".join(f"{i+1}. {rec}" for i, rec in enumerate(recommendations))

