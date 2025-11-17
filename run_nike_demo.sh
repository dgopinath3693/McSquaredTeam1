#!/bin/bash
# Nike.com Demo - One-Command Runner
# Run this from the repo root to execute the full Nike demo

cd /Users/ritvikgudlavalleti/McSquaredTeam1

echo "Installing dependencies..."
pip install -r URL_Crawler/requirements.txt > /dev/null 2>&1
pip install requests beautifulsoup4 pandas > /dev/null 2>&1

echo "Starting Nike.com AI Crawler Demo..."
echo "==========================================="
echo ""

python3 URL_Crawler/demo_ai_crawler_integrated.py \
  --csv URL_Crawler/nike_urls.csv \
  --bot-table AICrawlerLogging/bot_table.csv \
  --server-log AICrawlerLogging/server_log.csv \
  --limit 10

echo ""
echo "==========================================="
echo "Demo Complete!"
echo ""
echo "Output files created:"
echo "  - ai_crawler_store.json (normalized content)"
echo "  - ai_bot_analytics.json (bot activity)"
echo "  - ai_crawler_report.md (detailed report)"
echo ""
echo "To view results:"
echo "  cat ai_crawler_store.json | head -100"
echo "  cat ai_bot_analytics.json"
echo "  cat ai_crawler_report.md"
