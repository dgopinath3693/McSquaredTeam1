# Competitive Gap Analysis Demo

This enhanced demo performs **competitive content gap analysis** by comparing your entity's content with competitors' content.

## What It Does

1. **Crawls Your Content**: Fetches and normalizes content from your entity (classified as `owned_brand`)
2. **Crawls Competitors**: Fetches and normalizes competitor content (classified as `competitor`)
3. **Performs Gap Analysis**: Uses TF-IDF and cosine similarity to identify:
   - Keywords/topics competitors cover but you don't
   - Content opportunities where you're weak relative to competitors
   - Priority gaps (high/medium) based on competitor strength vs your coverage
4. **Generates Reports**: Creates detailed markdown report with recommendations

## Quick Start

### 1. Install Dependencies (first time only)

```bash
pip install scikit-learn numpy -q
# (beautifulsoup4, requests already installed)
```

### 2. Run with Test URLs

```bash
cd /Users/ritvikgudlavalleti/McSquaredTeam1

python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Your Brand" \
  --entity-csv URL_Crawler/test_entity_urls.csv \
  --competitor "Competitor 1" \
  --competitor-csv URL_Crawler/test_competitor_urls.csv \
  --limit 2
```

### 3. View Results

```bash
# View gap analysis
cat gap_analysis_results.json

# View coverage comparison
cat coverage_comparison.json

# View detailed report
cat competitive_gap_report.md
```

## Usage Examples

### Single Competitor Analysis

```bash
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike" \
  --entity-csv nike_urls.csv \
  --competitor "Adidas" \
  --competitor-csv adidas_urls.csv \
  --limit 10
```

### Multiple Competitors

```bash
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike" \
  --entity-csv nike_urls.csv \
  --competitor "Adidas" \
  --competitor-csv adidas_urls.csv \
  --competitor "Puma" \
  --competitor-csv puma_urls.csv \
  --limit 8
```

### With AI Bot Tracking

```bash
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike" \
  --entity-csv nike_urls.csv \
  --competitor "Adidas" \
  --competitor-csv adidas_urls.csv \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv \
  --limit 10
```

## How Gap Analysis Works

### TF-IDF Approach

1. **Vectorization**: Converts all content into TF-IDF vectors (term frequency vs inverse document frequency)
2. **Comparison**: Compares your vector against each competitor's vector
3. **Gap Scoring**: For each term:
   - Gap Score = (Competitor Strength) - (Your Strength)
   - Higher gap = competitor strong, you weak = opportunity
4. **Ranking**: Gaps sorted by score, top 15 returned

### Gap Priority

- **High**: Gap score > 0.1 (significant opportunity)
- **Medium**: Gap score ≤ 0.1 (incremental improvement)

### Example Output

```
1. sustainable manufacturing (Nike)
   Priority: High
   Adidas: 0.285
   Nike: 0.042
   Gap Score: 0.243

2. carbon neutral (Nike)
   Priority: High
   Adidas: 0.198
   Nike: 0.015
   Gap Score: 0.183

3. ethical sourcing (Nike)
   Priority: Medium
   Puma: 0.165
   Nike: 0.089
   Gap Score: 0.076
```

## Output Files

### gap_analysis_results.json
```json
{
  "owned_entity": "Nike",
  "competitors": ["Adidas", "Puma"],
  "total_gaps_identified": 15,
  "top_gaps": [
    {
      "term": "sustainable manufacturing",
      "competitor": "Adidas",
      "competitor_strength": 0.285,
      "owned_strength": 0.042,
      "gap_score": 0.243,
      "priority": "High"
    },
    ...
  ]
}
```

### coverage_comparison.json
```json
{
  "Nike": {
    "pages_crawled": 5,
    "total_words": 15234,
    "avg_words_per_page": 3046,
    "total_images": 42,
    "total_links": 156
  },
  "Adidas": {
    "pages_crawled": 5,
    "total_words": 18942,
    ...
  }
}
```

### competitive_gap_report.md
Human-readable markdown report with:
- Executive summary
- Coverage metrics per entity
- Top gaps table (term, competitor, priority, coverage %)
- Strategic recommendations

## Creating URL CSVs

**Format 1** (with header):
```csv
url
https://example.com
https://example.com/about
https://example.com/products
```

**Format 2** (plain URLs):
```
https://example.com
https://example.com/about
https://example.com/products
```

## Advanced Usage

### Analyze Different Product Lines

```bash
# Shoes category
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike Shoes" \
  --entity-csv nike_shoes_urls.csv \
  --competitor "Adidas Shoes" \
  --competitor-csv adidas_shoes_urls.csv \
  --limit 15

# Apparel category
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike Apparel" \
  --entity-csv nike_apparel_urls.csv \
  --competitor "Adidas Apparel" \
  --competitor-csv adidas_apparel_urls.csv \
  --limit 15
```

### Deep Dive on Specific Pages

Edit `test_entity_urls.csv` with specific URLs, then run with higher limit:

```bash
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Nike" \
  --entity-csv nike_detailed_urls.csv \
  --competitor "Adidas" \
  --competitor-csv adidas_detailed_urls.csv \
  --limit 50
```

## Interpretation Guide

### High Priority Gaps
- **Action**: Create dedicated content addressing these terms
- **Benefit**: Close competitive advantage gaps
- **Timeline**: 1-2 weeks

### Medium Priority Gaps
- **Action**: Enhance existing content with these terms
- **Benefit**: Incremental SEO/AI visibility improvements
- **Timeline**: Ongoing optimization

### Coverage Analysis
- **Total Words**: Content volume indicator
- **Avg Words/Page**: Content depth indicator
- **Images/Links**: Engagement and internal linking strategy

## Next Steps

1. **Run with test URLs**: Verify the demo works
2. **Create your CSVs**: Add real URLs for your brand and competitors
3. **Run analysis**: Execute the demo with your data
4. **Review report**: Analyze gap_analysis_results.json
5. **Plan content**: Use gaps to guide content strategy

## Requirements

```
beautifulsoup4
requests
pandas
scikit-learn
numpy
```

Install missing packages:
```bash
pip install scikit-learn numpy
```

## Troubleshooting

### "No module named sklearn"
```bash
pip install scikit-learn
```

### SSL errors when crawling
Use safe domains (example.com, httpbin.org) for testing

### Low gap scores
- Your content may be more comprehensive than competitors
- Try analyzing different entities or categories
- Increase --limit to get more content for analysis

## Integration with AI Bot Tracking

The demo also tracks AI bot interactions per entity, so you can see:
- Which bots crawl your content vs competitors'
- Content discovery patterns
- AI engine focus areas

View in output with `--bot-table` and `--server-log` flags.

---

**Ready to analyze?** Start with:
```bash
python3 URL_Crawler/demo_competitive_gap_analysis.py \
  --entity "Brand" \
  --entity-csv test_entity_urls.csv \
  --competitor "Competitor" \
  --competitor-csv test_competitor_urls.csv \
  --limit 2
```
