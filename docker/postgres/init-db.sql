-- init-db.sql
-- Create extensions and tables for AI crawler tracking

-- enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ai_bots reference table
CREATE TABLE IF NOT EXISTS ai_bots (
    bot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    provider TEXT,
    type TEXT,
    user_agent_pattern TEXT,
    ip_ranges JSONB,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_updated TIMESTAMPTZ DEFAULT now()
);

-- crawler_logs
CREATE TABLE IF NOT EXISTS crawler_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID REFERENCES ai_bots(bot_id) ON DELETE SET NULL,
    detected_name TEXT,
    detection_confidence TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    url TEXT NOT NULL,
    status_code INTEGER,
    method TEXT,
    response_time_ms DOUBLE PRECISION,
    user_agent TEXT,
    ip INET,
    referer TEXT,
    raw_log JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_crawler_logs_bot_time ON crawler_logs(bot_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_crawler_logs_url ON crawler_logs(url);
CREATE INDEX IF NOT EXISTS idx_crawler_logs_ts ON crawler_logs(timestamp);
