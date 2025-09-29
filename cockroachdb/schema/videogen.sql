-- cockroachdb/schema/videogen.sql
CREATE DATABASE IF NOT EXISTS videogen;
SET DATABASE = videogen;
CREATE TABLE IF NOT EXISTS jobs (
job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id UUID NOT NULL,
topic STRING NOT NULL CHECK (length(topic) BETWEEN 1 AND 500),
status STRING NOT NULL CHECK (status IN ('queued','processing','completed','failed')),
llm_provider STRING NOT NULL,
video_sources JSONB NOT NULL DEFAULT '[]'::JSONB,
estimated_cost_usd DECIMAL(10,4),
actual_cost_usd DECIMAL(10,4),
video_url STRING,
script_hash BYTES,
metadata_ciphertext STRING,
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
started_at TIMESTAMPTZ,
completed_at TIMESTAMPTZ,
processing_time_sec INT,
error_message STRING,
INDEX idx_user_status (user_id, status),
INDEX idx_created_at (created_at DESC),
INDEX idx_script_hash (script_hash) WHERE script_hash IS NOT NULL,
INDEX idx_cost (actual_cost_usd DESC) WHERE actual_cost_usd IS NOT NULL
);
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON jobs USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE TABLE IF NOT EXISTS audit_log (
log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
event_type STRING NOT NULL,
actor STRING NOT NULL,
details JSONB NOT NULL DEFAULT '{}'::JSONB,
timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
INDEX idx_job_events (job_id, timestamp),
INDEX idx_actor_events (actor, timestamp)
);
CREATE MATERIALIZED VIEW IF NOT EXISTS focus_index_hourly AS
SELECT
time_bucket('1 hour', completed_at) AS hour_bucket,
llm_provider,
COUNT(*) AS total_jobs,
AVG(processing_time_sec) AS avg_duration_sec,
SUM(actual_cost_usd) AS total_cost,
(
0.4 * (COUNT(*) FILTER (WHERE status='completed') / NULLIF(COUNT(*),0)::FLOAT) +
0.3 * LEAST(COUNT(*)::FLOAT / 100.0, 1.0) +
0.2 * (1.0 - COALESCE(SUM(actual_cost_usd) / NULLIF(SUM(estimated_cost_usd),0), 0)) -
0.1 * (COUNT(*) FILTER (WHERE processing_time_sec > 300) / NULLIF(COUNT(*),0)::FLOAT)
) AS focus_index
FROM jobs
WHERE completed_at IS NOT NULL
GROUP BY 1,2;
