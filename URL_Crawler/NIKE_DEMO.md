# Nike.com Demo - AI Crawler Tracking

This is a complete working example using Nike.com as the target site.

## Quick Start

### 1. Install Dependencies (first time only)

```bash
cd /Users/ritvikgudlavalleti/McSquaredTeam1
pip install -r URL_Crawler/requirements.txt
pip install requests beautifulsoup4 pandas
```

### 2. Run Demo with Nike URLs

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/nike_urls.csv \
  --limit 10
```

### 3. View Results

After running, check these files:

```bash
# View normalized content store
cat ai_crawler_store.json

# View AI bot analytics (if tracking enabled)
cat ai_bot_analytics.json

# View detailed report
cat ai_crawler_report.md
```

## Full Demo with Bot Tracking

If you want to also track AI bot activity from your logs:

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/nike_urls.csv \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv \
  --limit 10
```

## What the Demo Does

1. **Crawls Nike URLs**: Fetches each page from the CSV
2. **Extracts Content**: 
   - Title, headings, clean text
   - Metrics: word count, image count, links
   - Structured data (Schema.org, JSON-LD)
3. **Stores Normalized Documents**: Creates `ai_crawler_store.json`
4. **Tracks AI Bot Access** (optional): Matches paths with bot_table.csv
5. **Generates Reports**: Analytics and markdown report

## Example Output

### ai_crawler_store.json (sample)
```json
{
  "doc_id": "abc123...",
  "url": "https://www.nike.com/w/mens-shoes-nik1zy7ok",
  "domain": "www.nike.com",
  "entity_type": "owned_brand",
  "entity_name": "Target Site",
  "title": "Men's Shoes. Nike.com",
  "content_type": "product_page",
  "clean_text": "...",
  "metrics": {
    "word_count": 2543,
    "image_count": 45,
    "link_count": 156,
    "heading_count": 12
  },
  "crawl_metadata": {
    "crawled_at": "2025-11-17T...",
    "crawler_id": "ai-bot-tracker-v1",
    "response_code": 200,
    "response_time_ms": 1234,
    "detected_ai_bots": ["GPTBot", "Perplexity"]
  }
}
```

### ai_bot_analytics.json (sample)
```json
{
  "total_unique_bots": 5,
  "total_unique_urls_accessed": 8,
  "bots": {
    "GPTBot": {
      "interaction_count": 12,
      "unique_urls": 6
    },
    "PerplexityBot": {
      "interaction_count": 8,
      "unique_urls": 4
    }
  }
}
```

## Advanced: Using Website Mode

If you want the demo to discover links from Nike's homepage instead of using the CSV:

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --website https://www.nike.com \
  --limit 15
```

⚠️ **Note**: This may take longer as it crawls the homepage, discovers links, then crawls those pages.

## Performance Notes

- **Runtime**: ~5-10 seconds per page (with 0.5s delays between requests)
- **For 10 pages**: ~1-2 minutes total
- **Output size**: Each page ~50-200 KB in JSON format

## Troubleshooting

### SSL Certificate Error
```bash
# Add this before running if you hit SSL issues
export REQUESTS_CA_BUNDLE=""
```

### Rate Limiting (429 errors)
Increase the delay in the script or reduce `--limit`

### Memory Issues with Large Crawls
Keep `--limit` under 50 for large sites

## Next Steps

1. **Run the demo**: `python3 URL_Crawler/demo_ai_crawler_integrated.py --csv URL_Crawler/nike_urls.csv --limit 10`
2. **Inspect outputs**: Check `ai_crawler_store.json` for content
3. **Add bot tracking**: Re-run with `--bot-table` and `--server-log` flags
4. **Modify URLs**: Edit `nike_urls.csv` to add more Nike pages or other sites

## Command Reference

```bash
# Basic Nike crawl
python3 URL_Crawler/demo_ai_crawler_integrated.py --csv URL_Crawler/nike_urls.csv

# With bot tracking
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/nike_urls.csv \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv

# Different limit
python3 URL_Crawler/demo_ai_crawler_integrated.py --csv URL_Crawler/nike_urls.csv --limit 5

# Full help
python3 URL_Crawler/demo_ai_crawler_integrated.py --help
```

---

**Created**: November 17, 2025
**Target**: Nike.com product pages
**Use case**: Demo AI crawler tracking + content normalization
