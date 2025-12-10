# AICrawlerLogging

This module handles the ingestion, tracking, and analysis of AI bot interactions with websites. It bridges the gap between raw server logs and structured database records, enabling detection and analytics of which AI crawlers are accessing your web properties.

## Overview

The AICrawlerLogging component performs three key functions:

1. **Bot Definition Management**: Maintains a registry of known AI bots with detection patterns
2. **Log Ingestion**: Parses server logs and matches user-agents against known AI bot signatures
3. **Crawler Tracking**: Records which bots accessed which URLs and when

## Contents

### Core Files

- **`ingest.py`** - Main ingestion script that:
  - Reads `bot_table.csv` to seed the `ai_bots` database table with bot definitions
  - Parses `server_log.csv` entries and matches user-agents against bot patterns
  - Inserts matched events into the `crawler_logs` PostgreSQL table
  - Uses defensive parsing to handle varying CSV column headers

- **`tracking.py`** - Bot tracking and analytics module:
  - Loads bot definitions and server logs from CSV files
  - Matches HTTP interactions to known AI bots
  - Generates analytics reports on bot activity patterns
  - Outputs results to JSON format for downstream analysis

### Data Files

- **`bot_table.csv`** - Known AI bot definitions with columns:
  - Bot name/identifier
  - Provider information
  - Detection characteristics (user-agent patterns, IP ranges, etc.)

- **`server_log.csv`** - Raw server access logs containing:
  - Timestamps of HTTP requests
  - User-agent strings from requesters
  - URL paths accessed
  - HTTP response codes
  - Request metadata

### Configuration

- **`requirements.txt`** - Python dependencies:
  - `psycopg2` - PostgreSQL adapter for Python
  - `pandas` - Data manipulation and CSV handling

## Usage

### Quick Start with Docker

```bash
# From repository root
docker compose up -d

# Set environment variables
export DATABASE_URL="postgres://mcsq_user:mcsq_pass@localhost:5432/mcsq_db"

# Install dependencies
pip install -r AICrawlerLogging/requirements.txt

# Run ingestion
python3 AICrawlerLogging/ingest.py AICrawlerLogging/bot_table.csv AICrawlerLogging/server_log.csv
```

### With Existing PostgreSQL Database

```bash
# Set your database connection string
export DATABASE_URL="postgres://user:password@host:port/dbname"

# Run ingestion
python3 AICrawlerLogging/ingest.py bot_table.csv server_log.csv
```

## Database Schema

### `ai_bots` Table
Stores registered AI bot definitions:

```sql
CREATE TABLE ai_bots (
    bot_id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,        -- e.g., "Ahrefs", "Googlebot"
    provider VARCHAR(255),                     -- Bot provider/company
    type VARCHAR(50),                          -- e.g., "crawler", "aggregator"
    user_agent_pattern VARCHAR(1000),          -- Regex pattern for detection
    ip_ranges TEXT,                            -- CIDR notation IP ranges
    detection_accuracy FLOAT,                  -- 0-1 confidence score
    created_at TIMESTAMP DEFAULT NOW()
);
```

### `crawler_logs` Table
Records individual bot interactions:

```sql
CREATE TABLE crawler_logs (
    id BIGSERIAL PRIMARY KEY,
    bot_id UUID REFERENCES ai_bots(bot_id),
    timestamp TIMESTAMP NOT NULL,
    url VARCHAR(2000) NOT NULL,
    status_code INTEGER,
    user_agent VARCHAR(1000),
    ip_address VARCHAR(45),
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Features

- **Intelligent Bot Detection**: Matches user-agents and IP patterns to identify known AI crawlers
- **Defensive CSV Parsing**: Automatically maps common column name variations
- **Scalable Ingestion**: Handles large server log files efficiently with batch processing
- **Duplicate Handling**: Prevents duplicate entries in crawler logs
- **Confidence Scoring**: Records detection accuracy for bot identification

## Integration Points

- **Input**: Consumes `bot_table.csv` and `server_log.csv` from the AICrawlerLogging folder
- **Database**: Requires PostgreSQL instance (started via Docker or external)
- **Output**: Populated `ai_bots` and `crawler_logs` tables for downstream analytics
- **Upstream**: Used by `ContentGapAnalysis` and `FastAPIApp` for enriched analytics

## Common Issues & Solutions

**Issue**: "DATABASE_URL not set"
- **Solution**: Export DATABASE_URL before running: `export DATABASE_URL="postgres://..."`

**Issue**: "Connection refused"
- **Solution**: Ensure PostgreSQL is running: `docker compose ps` should show postgres container

**Issue**: Column header mismatch in CSV
- **Solution**: The script tries common header names automatically, but ensure your CSV contains fields for: date/timestamp, user-agent, URL

## Example Output

After successful ingestion, you can query tracked bots:

```sql
SELECT name, COUNT(*) as access_count 
FROM crawler_logs 
JOIN ai_bots ON crawler_logs.bot_id = ai_bots.bot_id 
GROUP BY name
ORDER BY access_count DESC;
```

## Next Steps

- Enhance detection rules with known bot user-agent patterns
- Implement IP-range verification for better accuracy
- Add visualization of bot activity patterns
- Integrate with FastAPI dashboard for real-time monitoring
