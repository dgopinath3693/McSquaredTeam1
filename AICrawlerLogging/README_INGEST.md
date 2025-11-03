Postgres Docker + ingestion guide

What I added
- docker/postgres/Dockerfile
- docker/postgres/init-db.sql (creates `ai_bots` and `crawler_logs` tables)
- docker-compose.yml (at repo root) to start the Postgres DB
- AICrawlerLogging/ingest.py - ingestion script to seed `ai_bots` from `bot_table.csv` and ingest `server_log.csv` into `crawler_logs`
- AICrawlerLogging/requirements.txt - Python deps for the ingestion script

Quick start (macOS, zsh)

1) If you have Docker installed

Build and run the DB container (from the repo root):

```bash
# build and start
docker compose up -d --build

# wait a few seconds and check status
docker compose ps
```

Postgres will be available at localhost:5432 with credentials from `docker-compose.yml`:
- user: mcsq_user
- password: mcsq_pass
- db: mcsq_db

Set the DATABASE_URL and run the ingestion script

```bash
export DATABASE_URL="postgres://mcsq_user:mcsq_pass@localhost:5432/mcsq_db"
python3 -m pip install -r AICrawlerLogging/requirements.txt
python3 AICrawlerLogging/ingest.py AICrawlerLogging/bot_table.csv AICrawlerLogging/server_log.csv
```

2) If you don't have Docker or prefer a hosted DB
- Create a Postgres instance (Cloud or local), obtain connection URL, then run the same commands after setting DATABASE_URL.

Notes about the ingestion script
- It seeds `ai_bots` from the `Bot` column in `bot_table.csv` and creates a naive user-agent regex based on the bot name.
- It parses `server_log.csv` row-wise and tries to match user-agent against the patterns in `ai_bots`. If matched, it sets `bot_id` and inserts a row into `crawler_logs`.
- The script is defensive regarding CSV headers and will try to map date/user-agent/url fields using common header names.

If you want, next I can:
- Improve detection rules (better regexes and known UA patterns),
- Add IP-range verification and detection confidence levels,
- Add unit tests and sample run verifying a local ingest with a temporary SQLite DB fallback.

