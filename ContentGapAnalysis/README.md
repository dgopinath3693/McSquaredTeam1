# ContentGapAnalysis

This module performs comprehensive competitive content gap analysis using TF-IDF vectorization and cosine similarity metrics. It compares your owned brand content against competitors to identify content gaps, coverage differences, and strategic opportunities.

## Overview

ContentGapAnalysis provides data-driven insights into:

- **Content Coverage Gaps**: Identifies topics competitors cover that you don't
- **Keyword Analysis**: Compares keyword frequency and presence across entities
- **Topic Modeling**: Uses TF-IDF to extract and compare important terms
- **Competitive Positioning**: Visualizes content strengths and weaknesses
- **Actionable Recommendations**: Suggests priority areas for content expansion

## Contents

### Core Files

- **`gapAnalysisImplementation.py`** - Main gap analysis engine:
  - TF-IDF calculation for content normalization
  - Cosine similarity computation between documents
  - Gap scoring (competitor content - owned brand content)
  - Coverage metrics calculation (pages, words, images, links)
  - JSON and Markdown report generation
  - Deduplication and content matching logic

- **`webscraper.py`** - Content collection and preprocessing:
  - Crawls websites to collect content
  - Normalizes and cleans extracted text
  - Handles different content types (text, structured data)
  - Prepares content for analysis

### Documentation

- **`Pseudo Code`** - High-level algorithm documentation:
  - Analysis workflow design
  - Similarity computation methods
  - Gap identification logic

## Setup

### Requirements

- Python 3.8+
- NumPy/Pandas for numerical computation
- Scikit-learn for TF-IDF and similarity metrics
- BeautifulSoup for web scraping (optional)

### Installation

```bash
cd ContentGapAnalysis
pip install numpy pandas scikit-learn beautifulsoup4 requests
```

## Usage

### Basic Gap Analysis

```python
from gapAnalysisImplementation import CompetitiveGapAnalyzer
from store import ContentStore

# Load content store
store = ContentStore("ai_crawler_store.json")

# Initialize analyzer
analyzer = CompetitiveGapAnalyzer(store)

# Perform analysis
gaps = analyzer.analyze_competitor_gaps(
    owned_brand="Nike",
    competitor="Adidas"
)

# Generate report
report = analyzer.generate_gap_report(gaps)
print(report)
```

### Command Line Usage

```bash
# Run gap analysis with output
python3 gapAnalysisImplementation.py \
  --owned-brand "Nike" \
  --competitor "Adidas" \
  --output gap_analysis_report.json
```

## Analysis Methods

### TF-IDF Vectorization

Converts document collections into numerical vectors representing term importance:

```
TF-IDF(t,d) = TF(t,d) × IDF(t)
```

- **TF**: How often a term appears in a document
- **IDF**: How unique/rare a term is across all documents
- **Result**: High scores for distinctive, important terms

### Cosine Similarity

Measures similarity between two documents on a 0-1 scale:

```
similarity = (A · B) / (||A|| × ||B||)
```

- **1.0**: Identical content
- **0.5**: Moderately similar
- **0.0**: Completely different

### Gap Scoring

Identifies content opportunities:

```
Gap Score = Competitor Content - Owned Brand Content
```

- **Positive**: Competitor has coverage you lack
- **Negative**: You have more coverage
- **Zero**: Equal coverage

## Output Format

### JSON Report

```json
{
  "analysis_metadata": {
    "owned_brand": "Nike",
    "competitor": "Adidas",
    "timestamp": "2025-01-10T10:30:45Z",
    "documents_analyzed": 150
  },
  "coverage_metrics": {
    "Nike": {
      "total_pages": 45,
      "total_words": 250000,
      "total_images": 180,
      "total_links": 520
    },
    "Adidas": {
      "total_pages": 52,
      "total_words": 280000,
      "total_images": 210,
      "total_links": 580
    }
  },
  "top_gaps": [
    {
      "topic": "sustainable manufacturing",
      "gap_score": 0.87,
      "competitor_coverage": 12,
      "owned_coverage": 2,
      "keywords": ["eco-friendly", "carbon neutral", "recycled materials"]
    }
  ],
  "keyword_analysis": {
    "unique_to_competitor": ["biotech", "innovation", "research"],
    "unique_to_owned": ["tradition", "heritage", "quality"],
    "shared_keywords": ["performance", "design", "customer"]
  }
}
```

### Markdown Report

Human-readable format with:
- Executive summary
- Key findings and gaps
- Coverage comparison tables
- Recommended actions
- Detailed analysis tables

## Key Metrics

### Coverage Metrics
- **Pages**: Total number of web pages analyzed
- **Words**: Total word count across all pages
- **Images**: Total images found and indexed
- **Links**: Total internal and external links

### Similarity Metrics
- **Average Similarity**: Mean cosine similarity between owned and competitor content
- **Top Similarity**: Highest similarity score for any document pair
- **Unique Topics**: Content areas present in only one entity

### Gap Metrics
- **Content Gap Score**: Aggregate gap across all dimensions
- **Priority Gaps**: High-scoring gaps warranting immediate attention
- **Quick Wins**: Easy-to-close gaps with high ROI

## Integration Points

### Upstream Dependencies

- **URL_Crawler**: Provides crawled content stored in `ai_crawler_store.json`
- **AICrawlerLogging**: Tracks which content was accessed by AI bots

### Downstream Usage

- **FastAPIApp**: Serves gap analysis results via REST API
- **Analytics**: Generates visualizations and dashboards
- **Strategy**: Informs content planning and competitive positioning

## Advanced Features

### Custom Topic Extraction

Define domain-specific topics for analysis:

```python
analyzer.custom_topics = {
    "sustainability": ["eco", "green", "sustainable", "carbon"],
    "innovation": ["ai", "machine learning", "automation", "tech"],
    "customer_experience": ["support", "service", "experience", "satisfaction"]
}
```

### Filtering and Normalization

```python
# Exclude pages below quality threshold
gaps = analyzer.analyze_competitor_gaps(
    min_word_count=100,
    exclude_navigation=True
)

# Focus on specific URL patterns
gaps = analyzer.analyze_competitor_gaps(
    url_pattern="/products.*"
)
```

## Performance Considerations

- **Large Datasets**: For 1000+ pages, consider batch processing
- **Memory Usage**: TF-IDF matrices scale with vocabulary size
- **Processing Time**: Similarity computation is O(n²) for n documents

## Example Analysis Workflow

```bash
# 1. Crawl competitor sites
python3 ../URL_Crawler/crawler.py \
  --website https://adidas.com \
  --entity-name "Adidas" \
  --entity-type "competitor"

# 2. Run gap analysis
python3 gapAnalysisImplementation.py \
  --owned-brand "Nike" \
  --competitor "Adidas" \
  --output gap_report.json

# 3. View results
cat gap_report.json | jq '.top_gaps'
```

## Troubleshooting

### Issue: "No documents to analyze"
- Ensure ContentStore has loaded documents
- Verify entity names match exactly (case-sensitive)
- Check that crawled content is stored in the correct format

### Issue: "Similarity scores all zero"
- Verify documents have sufficient word content
- Check vocabulary extraction is working
- Review minimum word count thresholds

### Issue: "Out of memory"
- Process in batches instead of all at once
- Reduce vocabulary size (filter common words)
- Use sparse matrix representation

## Next Steps

- Implement advanced NLP for semantic similarity
- Add temporal analysis to track gap evolution
- Create interactive dashboard for gap visualization
- Develop automated content recommendations engine
