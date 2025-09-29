-- services/video-generation/schema/video_jobs.sql
CREATE DATABASE IF NOT EXISTS videogen;
SET DATABASE = videogen;

CREATE TABLE IF NOT EXISTS jobs (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  topic STRING NOT NULL,
  status STRING NOT NULL CHECK (status IN ('queued','processing','completed','failed')),
  llm_provider STRING NOT NULL DEFAULT 'openai',
  estimated_cost_usd DECIMAL(10,4),
  actual_cost_usd DECIMAL(10,4),
  video_url STRING,
  script_hash BYTES,
  metadata_ciphertext STRING,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error_message STRING,
  INDEX idx_user_status (user_id, status),
  INDEX idx_created (created_at DESC),
  INDEX idx_script_hash (script_hash) WHERE script_hash IS NOT NULL
);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON jobs
  USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE TABLE IF NOT EXISTS audit_log (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(job_id) ON DELETE CASCADE,
  event_type STRING NOT NULL,
  actor STRING NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::JSONB,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX idx_job_id (job_id),
  INDEX idx_timestamp (timestamp DESC)
);

-- smoke insert
INSERT INTO jobs (user_id, topic, status, llm_provider, estimated_cost_usd)
VALUES (gen_random_uuid(), 'AI Security Trends', 'queued', 'openai', 0.015);