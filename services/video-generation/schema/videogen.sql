-- services/video-generation/schema/videogen.sql
-- Deploy: psql $COCKROACH_URL -f services/video-generation/schema/videogen.sql

CREATE DATABASE IF NOT EXISTS videogen;
SET DATABASE = videogen;

-- Main jobs table with comprehensive tracking
CREATE TABLE IF NOT EXISTS jobs (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Identity and routing
  user_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  spiffe_id STRING NOT NULL,  -- SVID that initiated the job

  -- Request details
  topic STRING NOT NULL CHECK (length(topic) > 0 AND length(topic) <= 500),
  script_hash BYTES,  -- SHA-256 of generated script for deduplication

  -- Provider selection (tracks which services were used)
  llm_provider STRING NOT NULL,
  tts_provider STRING NOT NULL,
  material_sources JSONB NOT NULL DEFAULT '[]'::JSONB,

  -- State machine
  status STRING NOT NULL CHECK (status IN (
    'queued', 'validating', 'generating_script', 'sourcing_materials',
    'synthesizing_voice', 'rendering', 'completed', 'failed', 'cancelled'
  )),

  -- Cost tracking with breakdown
  estimated_cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0,
  actual_cost_usd DECIMAL(10,6),
  cost_breakdown JSONB NOT NULL DEFAULT '{}'::JSONB,  -- per-service costs

  -- Output artifacts
  video_url STRING,
  video_size_bytes BIGINT,
  video_duration_sec DECIMAL(8,2),

  -- Encrypted metadata (via Vault Transit)
  -- Contains: full script, keywords, material URLs, internal routing details
  metadata_ciphertext STRING,
  metadata_key_version INT,

  -- Audit timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,

  -- Error handling
  error_message STRING,
  error_code STRING,
  retry_count INT NOT NULL DEFAULT 0,
  max_retries INT NOT NULL DEFAULT 3,

  -- Performance metrics
  queue_time_ms BIGINT,
  processing_time_ms BIGINT,

  -- Indexes for common query patterns
  INDEX idx_user_status (user_id, status),
  INDEX idx_tenant_created (tenant_id, created_at DESC),
  INDEX idx_status_created (status, created_at DESC),
  INDEX idx_script_hash (script_hash) WHERE script_hash IS NOT NULL,
  INDEX idx_spiffe (spiffe_id, created_at DESC)
);

-- Audit log for every state transition and significant event
CREATE TABLE IF NOT EXISTS audit_log (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

  -- Event classification
  event_type STRING NOT NULL CHECK (event_type IN (
    'job_created', 'status_changed', 'cost_updated', 'error_occurred',
    'retry_attempted', 'job_completed', 'job_cancelled', 'security_violation'
  )),

  -- Actor information (from JWT-SVID)
  actor_spiffe_id STRING NOT NULL,
  actor_ip INET,

  -- Event details
  old_status STRING,
  new_status STRING,
  details JSONB NOT NULL DEFAULT '{}'::JSONB,

  -- Provenance
  ledger_event_id UUID,  -- Reference to your main ledger
  merkle_root BYTES,

  -- Timestamp
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),

  INDEX idx_job_id (job_id, timestamp DESC),
  INDEX idx_event_type (event_type, timestamp DESC),
  INDEX idx_timestamp (timestamp DESC),
  INDEX idx_actor (actor_spiffe_id, timestamp DESC)
);

-- Cost aggregation view for metrics
CREATE VIEW job_costs AS
SELECT
  date_trunc('hour', completed_at) as hour,
  llm_provider,
  tts_provider,
  COUNT(*) as job_count,
  SUM(actual_cost_usd) as total_cost,
  AVG(actual_cost_usd) as avg_cost,
  SUM(processing_time_ms) as total_processing_ms
FROM jobs
WHERE status = 'completed' AND completed_at IS NOT NULL
GROUP BY 1, 2, 3;

-- Row-level security for multi-tenant isolation
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON jobs
  USING (
    tenant_id = current_setting('app.current_tenant_id')::UUID
    OR current_user = 'admin'
  );

-- Service account can read all for metrics
CREATE POLICY metrics_readonly ON jobs
  FOR SELECT
  USING (current_user = 'metrics_service');

-- Similar RLS for audit_log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_tenant_isolation ON audit_log
  USING (
    job_id IN (
      SELECT job_id FROM jobs
      WHERE tenant_id = current_setting('app.current_tenant_id')::UUID
    )
  );