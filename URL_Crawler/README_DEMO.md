# AI Crawler Tracking + URL Content Store Demo

This demo integrates URL crawling and storage with AI bot interaction tracking using the existing URL_Crawler infrastructure.

## Features

- **Flexible input**: Crawl a single website, discover internal links, or use a CSV of full URLs
- **Content storage**: Uses `ContentCrawler` and `ContentStore` to normalize and store page content
- **AI bot tracking**: Matches crawled pages with AI bot activity from `bot_table.csv` and `server_log.csv`
- **Analytics**: Generates summary of which AI bots accessed which pages
- **Output**: Stores normalized content in `ai_crawler_store.json` with AI bot metadata

## Usage

### Option 1: Crawl a website and auto-discover links

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --website https://example.com \
  --limit 10
```

This will:
1. Crawl the website homepage
2. Extract and crawl internal links (up to limit)
3. Store content in `ai_crawler_store.json`

### Option 2: Crawl a list of URLs from CSV

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv sample_urls.csv \
  --limit 20
```

CSV format (one of these):
- Simple: one URL per line (must start with `http`)
- With header: column named `url`, `URL`, or `Url`

### Option 3: Include AI bot tracking (with bot_table.csv and server_log.csv)

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --website https://example.com \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv \
  --limit 15
```

This will:
1. Crawl URLs from the website
2. Track which AI bots accessed pages (by matching paths from bot_table.csv)
3. Generate analytics about bot activity
4. Store results with AI bot metadata

## Output Files

- **ai_crawler_store.json**: Normalized content documents with metadata
- **ai_bot_analytics.json**: Summary of AI bot interactions
- **ai_crawler_report.md**: Detailed report with bot activity by page

## Requirements

```bash
pip install -r URL_Crawler/requirements.txt
pip install requests beautifulsoup4 pandas
```

## Example Commands

### Crawl a test site with 5 pages
```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --website https://www.wikipedia.org \
  --limit 5
```

### Crawl sample URLs
```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/sample_urls.csv \
  --limit 10
```

### Full demo with bot tracking
```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --website https://example.com \
  --limit 20 \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv
```

## How It Works

1. **URL Discovery**: Either use provided CSV or crawl website homepage to discover internal links
2. **Content Crawling**: `ContentCrawler` fetches each URL and extracts:
   - Title, headings, clean text
   - Metrics (word count, image count, links)
   - Structured data (JSON-LD, Schema.org)
3. **Storage**: `ContentStore` normalizes and stores documents with:
   - Unique document IDs
   - Content hash for deduplication
   - Extracted keywords (TF-IDF)
4. **AI Bot Tracking**: If bot_table.csv provided, extracts AI bot paths and matches them to crawled URLs
5. **Analytics**: Generates summary of bot activity and page coverage

## Notes

- The demo respects `robots.txt` implicitly through respectful delays (0.5s between requests)
- Bot tracking works by matching URL paths extracted from bot_table.csv with crawled page paths
- Larger crawls will take longer; use `--limit` to control scope
- Content is stored incrementally in JSON format for easy inspection
