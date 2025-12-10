# McSquaredTeam1

## Authors
- Diya Gopinath
- Akshaya Somasundaran
- Harsh Kadodwala
- Ritvik Gudlavalleti

## Overview
Repository holding all code realted to the McSqaured Team 1's code for the GEO dashboard backend

## Core Components

### URL_Crawler
Discovers and crawls URLs from target websites. Handles sitemap parsing, link extraction, and deduplication.

### AiExtractionAgent
Extracts content using Selenium WebDriver and Google Gemini API. Handles JavaScript-rendered pages. Outputs structured CSV data.

### PromptAgent
Manages LLM prompts for content analysis. Handles prompt generation and response processing.

### AICrawlerLogging
Tracks AI bot access to websites. Parses server logs, matches user-agents to known bots, stores results in PostgreSQL.

### ContentGapAnalysis
Compares content between brands using TF-IDF and cosine similarity. Identifies coverage gaps and generates reports (JSON/Markdown).

### FastAPIApp
REST API built with FastAPI and PostgreSQL. Provides endpoints for Items, Users, Logs, and analytics queries.

## Technology Stack

- **Language**: Python 3.8+
- **Web Framework**: FastAPI
- **Database**: PostgreSQL
- **AI**: Google Gemini API
- **Web Scraping**: Selenium, BeautifulSoup
- **ML**: Scikit-learn (TF-IDF, cosine similarity)
- **Containerization**: Docker

## Setup

### Database

```bash
docker compose up -d
```

PostgreSQL runs on `localhost:5432` (user: `mcsq_user`, password: `mcsq_pass`, db: `mcsq_db`)

### API

```bash
pip3 install "fastapi[standard]"
# Production:
pip3 install fastapi uvicorn[standard] gunicorn
```

### Component Dependencies

```bash
# AiExtractionAgent
pip install selenium google-generativeai

# ContentGapAnalysis
pip install numpy pandas scikit-learn

# AICrawlerLogging
pip install psycopg2 pandas
```

## Usage

### Run Gap Analysis

```bash
python3 ContentGapAnalysis/gapAnalysisImplementation.py \
  --owned-brand "Nike" \
  --competitor "Adidas" \
  --output gap_report.json
```

### Run Bot Tracking

```bash
export DATABASE_URL="postgres://mcsq_user:mcsq_pass@localhost:5432/mcsq_db"
python3 AICrawlerLogging/ingest.py \
  AICrawlerLogging/bot_table.csv \
  AICrawlerLogging/server_log.csv
```

### Start API

```bash
cd FastAPIApp
python3 -m uvicorn main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

## Data Flow

```
URL_Crawler → ai_crawler_store.json
     ↓
AiExtractionAgent → ai_responses_extracted.csv
     ↓
AICrawlerLogging → PostgreSQL (crawler_logs, ai_bots)
     ↓
ContentGapAnalysis → gap_analysis_results.json, competitive_gap_report.md
     ↓
FastAPIApp → REST API (Items, Users, Logs, Analytics)
```

## Output Files

- `ai_crawler_store.json` - Crawled content
- `ai_responses_extracted.csv` - AI-extracted data
- `gap_analysis_results.json` - Gap analysis metrics
- `competitive_gap_report.md` - Human-readable report
- `ai_bot_analytics.json` - Bot activity analytics
- `coverage_comparison.json` - Coverage metrics

## API Endpoints

- `GET /items/` - List items
- `POST /items/` - Create item
- `GET /users/` - List users
- `POST /logs/` - Create log
- `GET /analytics/gaps` - Gap analysis results
- `GET /health` - Health check

## Repository Structure

```
McSquaredTeam1/
├── URL_Crawler/              # URL discovery and crawling
├── AiExtractionAgent/        # AI content extraction
├── PromptAgent/              # LLM prompt management
├── AICrawlerLogging/         # Bot tracking
├── ContentGapAnalysis/       # Competitive analysis
├── FastAPIApp/               # REST API
├── docker/postgres/          # Database config
├── docker-compose.yml        # Container orchestration
└── run_nike_demo.sh          # Demo script
```

## Database Schema

### ai_bots
- `bot_id`, `name`, `provider`, `user_agent_pattern`, `ip_ranges`

### crawler_logs
- `id`, `bot_id`, `timestamp`, `url`, `status_code`, `user_agent`

### items
- `id`, `name`, `description`, `created_at`, `updated_at`

### users
- `id`, `email`, `name`, `created_at`

### logs
- `id`, `event_type`, `message`, `created_at`

---

**Repository**: https://github.com/dgopinath3693/McSquaredTeam1  
**Project**: McSquared Capstone - Fall 2025