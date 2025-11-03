"""
Ingest script for AI crawler tracking.
- Reads `bot_table.csv` to seed `ai_bots` table (simple patterns created if missing)
- Reads `server_log.csv` and matches user-agent against ai_bots.user_agent_pattern
- Inserts parsed events into `crawler_logs` table

Usage:
  - Set DATABASE_URL env var (e.g., postgres://mcsq_user:mcsq_pass@localhost:5432/mcsq_db)
  - Or run with SQLITE fallback: sqlite:///tmp/crawler.db

This script is defensive: it will try to map columns sensibly based on CSV headers.
"""

import os
import re
import csv
import json
import sys
from urllib.parse import urlparse
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd

DB_URL = os.environ.get('DATABASE_URL', 'postgres://mcsq_user:mcsq_pass@localhost:5432/mcsq_db')

# Helpers

def connect_db(url=DB_URL):
    # psycopg2 wants a libpq connection string or params
    # if sqlite requested, we won't attempt here; keep minimal for Postgres
    parsed = urlparse(url)
    if parsed.scheme.startswith('sqlite'):
        raise RuntimeError('SQLite fallback is not supported by psycopg2 in this script. Use a Postgres DB or change code to use sqlite3.')
    conn = psycopg2.connect(url)
    conn.autocommit = True
    return conn


def ensure_ai_bots_seed(conn, bot_table_csv):
    """Read bot_table.csv, extract distinct bot names and insert into ai_bots if not exist.
    Uses a naive user_agent_pattern based on the bot name (case-insensitive substring match).
    """
    df = pd.read_csv(bot_table_csv)
    if 'Bot' not in df.columns:
        print('bot_table.csv has no "Bot" column. Nothing to seed.')
        return
    bots = sorted(df['Bot'].dropna().unique())

    cur = conn.cursor()
    # Upsert simple entries
    for bot in bots:
        name = str(bot).strip()
        if not name:
            continue
        # naive regex: escape and allow case-insensitive
        pattern = '(?i)' + re.escape(name)
        # check exists by name
        cur.execute("SELECT bot_id FROM ai_bots WHERE name = %s", (name,))
        if cur.fetchone():
            # optionally update pattern if empty
            cur.execute("UPDATE ai_bots SET user_agent_pattern = COALESCE(user_agent_pattern, %s), last_updated=now() WHERE name=%s", (pattern, name))
        else:
            cur.execute(
                "INSERT INTO ai_bots (name, provider, type, user_agent_pattern, created_at, last_updated) VALUES (%s, %s, %s, %s, now(), now())",
                (name, None, 'unknown', pattern)
            )
    cur.close()
    print(f'Seeded/updated {len(bots)} bots from {bot_table_csv}')


def load_ai_bots_patterns(conn):
    cur = conn.cursor()
    cur.execute("SELECT bot_id, name, user_agent_pattern FROM ai_bots")
    rows = cur.fetchall()
    cur.close()
    patterns = []
    for bot_id, name, pat in rows:
        if pat:
            try:
                regex = re.compile(pat)
            except Exception:
                regex = re.compile(re.escape(name), re.I)
        else:
            regex = re.compile(re.escape(name), re.I)
        patterns.append((bot_id, name, regex))
    return patterns


def parse_row_to_event(row):
    # Accepts a dict-like row. Attempt to normalize fields.
    # Look for common fields: timestamp, Date, date, time, user_agent, User-Agent, ip, IP, Page path, url, path, status, status_code
    timestamp = None
    for k in ['timestamp','time','date','Date','Timestamp']:
        if k in row and pd.notna(row[k]):
            try:
                timestamp = pd.to_datetime(row[k])
            except Exception:
                try:
                    timestamp = datetime.fromisoformat(str(row[k]))
                except Exception:
                    timestamp = None
            break
    if timestamp is None:
        timestamp = datetime.utcnow()

    user_agent = None
    for k in ['user_agent','User-Agent','useragent','Bot','bot','agent']:
        if k in row and pd.notna(row[k]):
            user_agent = str(row[k])
            break

    url = None
    for k in ['url','URL','Page path','path','request','Request']:
        if k in row and pd.notna(row[k]):
            url = str(row[k])
            break
    if not url:
        url = '/'

    status = None
    for k in ['status','status_code','Response status codes','Response Status','code']:
        if k in row and pd.notna(row[k]):
            try:
                status = int(row[k])
            except Exception:
                try:
                    status = int(str(row[k]).split()[0])
                except Exception:
                    status = None
            break

    ip = None
    for k in ['ip','IP','remote_addr','client']:
        if k in row and pd.notna(row[k]):
            ip = str(row[k])
            break

    return {
        'timestamp': timestamp,
        'user_agent': user_agent,
        'url': url,
        'status_code': status,
        'ip': ip,
        'raw': row
    }


def ingest_server_logs(conn, server_log_csv, batch=500):
    # load ai bot patterns
    patterns = load_ai_bots_patterns(conn)
    cur = conn.cursor()
    # Read CSV with pandas for resilience
    df = pd.read_csv(server_log_csv, dtype=str)
    total = 0
    to_insert = []
    for _, row in df.iterrows():
        evt = parse_row_to_event(row)
        matched = None
        matched_name = None
        confidence = 'low'
        ua = evt['user_agent'] or ''
        for bot_id, name, regex in patterns:
            try:
                if ua and regex.search(ua):
                    matched = bot_id
                    matched_name = name
                    confidence = 'high'
                    break
            except Exception:
                continue
        if not matched:
            # try to match by Bot column if present in the row
            if 'Bot' in row and pd.notna(row['Bot']):
                bot_candidate = str(row['Bot'])
                for bot_id, name, regex in patterns:
                    if bot_candidate.lower() == name.lower():
                        matched = bot_id
                        matched_name = name
                        confidence = 'medium'
                        break
        # Build insert tuple
        tup = (
            matched,  # bot_id
            matched_name,
            confidence,
            evt['timestamp'],
            evt['url'],
            evt['status_code'],
            None,  # method
            None,  # response_time_ms
            ua,
            evt['ip'],
            None,
            json.dumps(evt['raw'].to_dict()) if hasattr(evt['raw'], 'to_dict') else json.dumps(dict(evt['raw']))
        )
        to_insert.append(tup)
        total += 1
        if len(to_insert) >= batch:
            execute_values(cur, """
                INSERT INTO crawler_logs (bot_id, detected_name, detection_confidence, timestamp, url, status_code, method, response_time_ms, user_agent, ip, referer, raw_log)
                VALUES %s
            """, to_insert)
            to_insert = []
    if to_insert:
        execute_values(cur, """
            INSERT INTO crawler_logs (bot_id, detected_name, detection_confidence, timestamp, url, status_code, method, response_time_ms, user_agent, ip, referer, raw_log)
            VALUES %s
        """, to_insert)
    cur.close()
    print(f'Ingested {total} log rows from {server_log_csv}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python ingest.py <bot_table.csv> <server_log.csv>')
        sys.exit(1)
    bot_csv = sys.argv[1]
    log_csv = sys.argv[2]
    try:
        conn = connect_db()
    except Exception as e:
        print('Failed to connect to Postgres DB at', DB_URL)
        print('Error:', e)
        print('If you intended to run against Postgres container, ensure container is running and DATABASE_URL is set.')
        sys.exit(2)

    ensure_ai_bots_seed(conn, bot_csv)
    ingest_server_logs(conn, log_csv)
    conn.close()
