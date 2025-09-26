-- Fortress v4 Ledger Schema Enhancements
-- Migration: 001_fortress_v4_ledger_indexes.sql
-- Purpose: Optimize ledger table performance and add Fortress v4 policy support

BEGIN;

-- Create ledger schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS ledger;

-- Create or enhance the main entries table
CREATE TABLE IF NOT EXISTS ledger.entries (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subject VARCHAR(256) NOT NULL,
    payload BYTEA NOT NULL,
    sig BYTEA NOT NULL,
    pubkey BYTEA NOT NULL,
    meta JSONB DEFAULT '{}',
    
    -- Fortress v4 enhancements
    policy_version VARCHAR(32) DEFAULT '4.0.0',
    audit_trail JSONB DEFAULT '{}',
    verification_status VARCHAR(32) DEFAULT 'pending',
    
    -- Constraints
    CONSTRAINT valid_subject CHECK (subject != '' AND length(subject) <= 256),
    CONSTRAINT valid_payload CHECK (length(payload) > 0 AND length(payload) <= 1048576), -- 1MB limit
    CONSTRAINT valid_policy_version CHECK (policy_version ~ '^[0-9]+\.[0-9]+\.[0-9]+$'),
    CONSTRAINT valid_verification_status CHECK (verification_status IN ('pending', 'verified', 'failed', 'disputed'))
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_ledger_entries_created_at ON ledger.entries (created_at);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_subject ON ledger.entries (subject);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_policy_version ON ledger.entries (policy_version);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_verification_status ON ledger.entries (verification_status);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_ledger_entries_subject_created_at ON ledger.entries (subject, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_status_created_at ON ledger.entries (verification_status, created_at DESC);

-- JSONB indexes for metadata queries
CREATE INDEX IF NOT EXISTS idx_ledger_entries_meta_gin ON ledger.entries USING GIN (meta);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_audit_gin ON ledger.entries USING GIN (audit_trail);

-- Partial indexes for active/recent entries
CREATE INDEX IF NOT EXISTS idx_ledger_entries_recent_verified 
ON ledger.entries (created_at DESC) 
WHERE verification_status = 'verified' AND created_at > NOW() - INTERVAL '30 days';

-- Create policy violations audit table
CREATE TABLE IF NOT EXISTS ledger.policy_violations (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entry_id BIGINT REFERENCES ledger.entries(id),
    policy_type VARCHAR(64) NOT NULL,
    policy_version VARCHAR(32) NOT NULL,
    violation_rules TEXT[] NOT NULL,
    client_ip INET,
    user_agent TEXT,
    request_context JSONB DEFAULT '{}',
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    
    CONSTRAINT valid_policy_type CHECK (policy_type IN ('ledger', 'api', 'runtime')),
    CONSTRAINT valid_violation_rules CHECK (array_length(violation_rules, 1) > 0)
);

-- Indexes for policy violations
CREATE INDEX IF NOT EXISTS idx_policy_violations_created_at ON ledger.policy_violations (created_at);
CREATE INDEX IF NOT EXISTS idx_policy_violations_policy_type ON ledger.policy_violations (policy_type);
CREATE INDEX IF NOT EXISTS idx_policy_violations_entry_id ON ledger.policy_violations (entry_id);
CREATE INDEX IF NOT EXISTS idx_policy_violations_client_ip ON ledger.policy_violations (client_ip);
CREATE INDEX IF NOT EXISTS idx_policy_violations_unresolved ON ledger.policy_violations (created_at) WHERE resolved_at IS NULL;

-- Create rate limiting tracking table
CREATE TABLE IF NOT EXISTS ledger.rate_limits (
    client_id VARCHAR(256) PRIMARY KEY,
    request_count INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    window_duration INTERVAL NOT NULL DEFAULT INTERVAL '1 minute',
    limit_exceeded_count INTEGER DEFAULT 0,
    first_request_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_request_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT positive_request_count CHECK (request_count >= 0),
    CONSTRAINT positive_limit_exceeded CHECK (limit_exceeded_count >= 0)
);

-- Indexes for rate limiting
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start ON ledger.rate_limits (window_start);
CREATE INDEX IF NOT EXISTS idx_rate_limits_last_request ON ledger.rate_limits (last_request_at);

-- Create system metrics table for runtime monitoring
CREATE TABLE IF NOT EXISTS ledger.system_metrics (
    id BIGSERIAL PRIMARY KEY,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metric_type VARCHAR(64) NOT NULL,
    metric_name VARCHAR(128) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(32),
    tags JSONB DEFAULT '{}',
    threshold_exceeded BOOLEAN DEFAULT FALSE,
    alert_level VARCHAR(16) DEFAULT 'info',
    
    CONSTRAINT valid_metric_type CHECK (metric_type IN ('memory', 'cpu', 'network', 'database', 'application')),
    CONSTRAINT valid_alert_level CHECK (alert_level IN ('info', 'warning', 'critical')),
    CONSTRAINT positive_metric_value CHECK (metric_value >= 0)
);

-- Indexes for system metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON ledger.system_metrics (recorded_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_type_name ON ledger.system_metrics (metric_type, metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_alerts ON ledger.system_metrics (recorded_at) WHERE threshold_exceeded = true;
CREATE INDEX IF NOT EXISTS idx_system_metrics_tags_gin ON ledger.system_metrics USING GIN (tags);

-- Partitioning for large datasets (optional, uncomment if needed)
-- CREATE TABLE ledger.entries_2024 PARTITION OF ledger.entries
-- FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Create views for common queries
CREATE OR REPLACE VIEW ledger.recent_entries AS
SELECT 
    id,
    created_at,
    subject,
    length(payload) as payload_size,
    policy_version,
    verification_status,
    meta,
    audit_trail
FROM ledger.entries 
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

CREATE OR REPLACE VIEW ledger.policy_violation_summary AS
SELECT 
    policy_type,
    policy_version,
    COUNT(*) as total_violations,
    COUNT(DISTINCT client_ip) as unique_clients,
    COUNT(*) FILTER (WHERE resolved_at IS NULL) as unresolved_violations,
    MIN(created_at) as first_violation,
    MAX(created_at) as last_violation
FROM ledger.policy_violations 
GROUP BY policy_type, policy_version
ORDER BY total_violations DESC;

-- Create functions for common operations
CREATE OR REPLACE FUNCTION ledger.log_policy_violation(
    p_entry_id BIGINT,
    p_policy_type VARCHAR(64),
    p_policy_version VARCHAR(32),
    p_violation_rules TEXT[],
    p_client_ip INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_request_context JSONB DEFAULT '{}'
) RETURNS BIGINT AS $$
DECLARE
    violation_id BIGINT;
BEGIN
    INSERT INTO ledger.policy_violations (
        entry_id, policy_type, policy_version, violation_rules, 
        client_ip, user_agent, request_context
    ) VALUES (
        p_entry_id, p_policy_type, p_policy_version, p_violation_rules,
        p_client_ip, p_user_agent, p_request_context
    ) RETURNING id INTO violation_id;
    
    RETURN violation_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to update rate limits
CREATE OR REPLACE FUNCTION ledger.update_rate_limit(
    p_client_id VARCHAR(256),
    p_window_duration INTERVAL DEFAULT INTERVAL '1 minute'
) RETURNS INTEGER AS $$
DECLARE
    current_count INTEGER;
    current_window TIMESTAMPTZ;
BEGIN
    -- Get current timestamp
    current_window := NOW();
    
    -- Upsert rate limit record
    INSERT INTO ledger.rate_limits (client_id, request_count, window_start, window_duration, last_request_at)
    VALUES (p_client_id, 1, current_window, p_window_duration, current_window)
    ON CONFLICT (client_id) DO UPDATE SET
        request_count = CASE 
            WHEN ledger.rate_limits.window_start + ledger.rate_limits.window_duration < current_window THEN 1
            ELSE ledger.rate_limits.request_count + 1
        END,
        window_start = CASE 
            WHEN ledger.rate_limits.window_start + ledger.rate_limits.window_duration < current_window THEN current_window
            ELSE ledger.rate_limits.window_start
        END,
        last_request_at = current_window,
        window_duration = p_window_duration
    RETURNING request_count INTO current_count;
    
    RETURN current_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to record system metrics
CREATE OR REPLACE FUNCTION ledger.record_metric(
    p_metric_type VARCHAR(64),
    p_metric_name VARCHAR(128),
    p_metric_value NUMERIC,
    p_metric_unit VARCHAR(32) DEFAULT NULL,
    p_tags JSONB DEFAULT '{}',
    p_threshold NUMERIC DEFAULT NULL,
    p_alert_level VARCHAR(16) DEFAULT 'info'
) RETURNS BIGINT AS $$
DECLARE
    metric_id BIGINT;
    threshold_exceeded BOOLEAN DEFAULT FALSE;
BEGIN
    -- Check if threshold is exceeded
    IF p_threshold IS NOT NULL AND p_metric_value > p_threshold THEN
        threshold_exceeded := TRUE;
    END IF;
    
    INSERT INTO ledger.system_metrics (
        metric_type, metric_name, metric_value, metric_unit, tags, 
        threshold_exceeded, alert_level
    ) VALUES (
        p_metric_type, p_metric_name, p_metric_value, p_metric_unit, p_tags,
        threshold_exceeded, p_alert_level
    ) RETURNING id INTO metric_id;
    
    RETURN metric_id;
END;
$$ LANGUAGE plpgsql;

-- Create cleanup job for old data (run periodically)
CREATE OR REPLACE FUNCTION ledger.cleanup_old_data(
    p_retention_days INTEGER DEFAULT 90
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cleanup_date TIMESTAMPTZ;
BEGIN
    cleanup_date := NOW() - (p_retention_days || ' days')::INTERVAL;
    
    -- Clean up old policy violations (keep only unresolved or recent)
    DELETE FROM ledger.policy_violations 
    WHERE created_at < cleanup_date AND resolved_at IS NOT NULL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old system metrics (keep only recent and alerts)
    DELETE FROM ledger.system_metrics 
    WHERE recorded_at < cleanup_date AND threshold_exceeded = FALSE;
    
    -- Clean up old rate limit records
    DELETE FROM ledger.rate_limits 
    WHERE last_request_at < cleanup_date;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE ledger.entries IS 'Main ledger entries table with Fortress v4 policy support';
COMMENT ON TABLE ledger.policy_violations IS 'Audit trail for policy violations';
COMMENT ON TABLE ledger.rate_limits IS 'Rate limiting tracking per client';
COMMENT ON TABLE ledger.system_metrics IS 'System performance and security metrics';

COMMENT ON COLUMN ledger.entries.policy_version IS 'Version of Fortress policies used for validation';
COMMENT ON COLUMN ledger.entries.audit_trail IS 'JSONB field storing policy evaluation details';
COMMENT ON COLUMN ledger.entries.verification_status IS 'Cryptographic verification status';

-- Grant permissions (adjust as needed for your setup)
GRANT USAGE ON SCHEMA ledger TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA ledger TO PUBLIC;
GRANT INSERT, UPDATE ON ledger.entries TO app_user;
GRANT INSERT ON ledger.policy_violations TO app_user;
GRANT INSERT, UPDATE ON ledger.rate_limits TO app_user;
GRANT INSERT ON ledger.system_metrics TO app_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ledger TO app_user;

COMMIT;