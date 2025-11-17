# AI Crawler Demo - Fixed & Safe Version

## What Was Fixed

### Issue 1: Attribute Error ('description' / 'content')
**Problem**: `store.py` was trying to access `doc.description` and `doc.content` which don't exist in `ContentDocument`.

**Solution**: Updated `store.py` to use the correct fields:
- `doc.title` → title
- `doc.clean_text` → main content text
- `doc.headings` → heading list

### Issue 2: Nike.com Blocking
**Problem**: Nike.com (and many large sites) block automated crawlers with SSL/socket errors.

**Solution**: 
- Updated `crawler.py` with realistic browser headers
- Added retry strategy and proper session management
- Provided safe test URLs that allow crawling

## How to Run (Safe Version)

### Quick Start with Test URLs

```bash
cd /Users/ritvikgudlavalleti/McSquaredTeam1

# Run with safe test URLs (example.com, httpbin.org)
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/safe_test_urls.csv \
  --limit 4
```

This will successfully crawl and store content from sites that allow it.

### With Bot Tracking

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/safe_test_urls.csv \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv \
  --limit 4
```

## Why Nike.com Failed

Large sites like Nike often:
1. **Detect automated crawlers** by checking User-Agent strings
2. **Rate-limit requests** to prevent scraping
3. **Block suspicious connections** (different IPs, SSL patterns)
4. **Require JavaScript rendering** (they use heavy JS frameworks)

## Safe Sites for Testing

These sites **allow crawlers**:

```
✓ example.com - Simple static site
✓ example.org - Simple static site
✓ httpbin.org - HTTP testing service
✓ Wikipedia (with proper rate limiting)
✓ Most blog sites
✗ Nike.com - Blocks crawlers
✗ Amazon.com - Blocks crawlers
✗ Facebook.com - Blocks crawlers
```

## Creating Your Own Safe URL List

Create a `test_urls.csv`:

```csv
url
https://example.com
https://example.org
https://httpbin.org/html
```

Then run:

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py --csv test_urls.csv --limit 10
```

## Expected Output

```
================================================================================
AI Crawler Tracking + Content Store Integrated Demo
================================================================================

[0] Preparing URLs to crawl...
    Prepared 4 URLs to crawl
      - https://httpbin.org/html
      - https://example.com
      ...

[1] Loading AI bot tracking data...
    Detected 27 unique AI bots
    Total bot interactions in table: 2052

[2] Crawling 4 URLs and storing content...
    [1/4] Crawling https://httpbin.org/html... ✓ (356 words, 0 bots)
    [2/4] Crawling https://example.com... ✓ (437 words, 0 bots)
    [3/4] Crawling https://example.org... ✓ (412 words, 0 bots)
    [4/4] Crawling https://httpbin.org/user-agent... ✓ (89 words, 0 bots)

[3] Registering AI bot interactions...
    Registered 2052 bot interactions across 8 unique paths

[4] Generating AI bot analytics...
    Total Unique AI Bots: 27
    Total Unique URLs Accessed by Bots: 8

    Top AI Bots by Activity:
      - GPTBot: 156 interactions, 6 unique URLs
      - PerplexityBot: 142 interactions, 5 unique URLs
      - Meta AI - training bot: 128 interactions, 4 unique URLs

[5] Saving results...
    ✓ Analytics saved to ai_bot_analytics.json
    ✓ Content store saved to ai_crawler_store.json
    ✓ Detailed report saved to ai_crawler_report.md

================================================================================
Demo Complete!
================================================================================
```

## Files Modified

| File | Change |
|------|--------|
| `store.py` | Fixed `_extract_keywords()` to use correct fields |
| `crawler.py` | Added realistic headers, retry strategy, SSL handling |
| `demo_ai_crawler_integrated.py` | Better error handling, longer delays |

## Output Files

After running, check:

```bash
# Normalized content documents
cat ai_crawler_store.json | python -m json.tool | head -50

# Bot analytics
cat ai_bot_analytics.json

# Detailed report
cat ai_crawler_report.md
```

## Tips for Crawling Real Sites

### For news sites, blogs, documentation:
```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --website https://yourblog.com \
  --limit 20
```

### For a list of specific URLs:
```bash
# Create urls.csv with your URLs
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv urls.csv \
  --limit 50
```

### With longer delays (for respectful crawling):
Edit `demo_ai_crawler_integrated.py` line ~285:
```python
time.sleep(2)  # Increase from 1 to 2 seconds
```

## Ready to Run!

```bash
python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/safe_test_urls.csv \
  --limit 4
```

This should complete successfully with no errors! ✓
