-- Database enhancements for Rekor anchoring workflow
-- This file contains recommended schema changes for optimal performance

-- Ensure the ledger schema and table exist
CREATE SCHEMA IF NOT EXISTS ledger;

-- The main entries table (if it doesn't exist)
-- Note: This assumes the table structure from services/ledger/server.go
CREATE TABLE IF NOT EXISTS ledger.entries (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    payload BYTEA NOT NULL,
    hash VARCHAR(64), -- SHA256 hex string (32 bytes * 2 for hex encoding)
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sig BYTEA,
    pubkey TEXT,
    meta JSONB
);

-- Recommended indexes for Rekor anchoring workflow performance

-- 1. Index on timestamp (descending) for efficient "ORDER BY ts DESC" queries
-- This is crucial for the workflow's query that gets the latest hashes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ledger_ts_desc 
    ON ledger.entries (ts DESC);

-- 2. Index on hash for lookups and deduplication
-- This helps with hash existence checks and prevents duplicate processing
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ledger_hash 
    ON ledger.entries (hash) 
    WHERE hash IS NOT NULL;

-- 3. Composite index for filtered queries (hash + timestamp)
-- Useful for more complex filtering scenarios in the future
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ledger_hash_ts 
    ON ledger.entries (hash, ts DESC) 
    WHERE hash IS NOT NULL;

-- Optional: Add a unique constraint on hash if ingestion process guarantees uniqueness
-- Uncomment this if you want to prevent duplicate hashes at the database level
-- ALTER TABLE ledger.entries ADD CONSTRAINT unique_hash UNIQUE (hash);

-- View for Rekor anchoring workflow queries
-- This encapsulates the filtering logic and makes queries more maintainable
CREATE OR REPLACE VIEW ledger.anchoring_candidates AS
SELECT DISTINCT 
    hash,
    ts,
    subject
FROM ledger.entries 
WHERE 
    hash IS NOT NULL 
    AND length(hash) = 64  -- SHA256 length check (64 hex chars = 32 bytes)
    AND hash ~ '^[a-f0-9]+$'  -- Valid lowercase hex format
ORDER BY ts DESC;

-- Function to get hashes for anchoring with proper limit handling
-- This provides a clean interface for the workflow to call
CREATE OR REPLACE FUNCTION ledger.get_anchoring_hashes(
    hash_limit INTEGER DEFAULT 1000
)
RETURNS TABLE(hash VARCHAR(64), ts TIMESTAMP, subject VARCHAR(255)) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ac.hash, 
        ac.ts, 
        ac.subject
    FROM ledger.anchoring_candidates ac
    LIMIT hash_limit;
END;
$$ LANGUAGE plpgsql;

-- Performance monitoring view
-- Helps track the effectiveness of indexes and query performance
CREATE OR REPLACE VIEW ledger.anchoring_stats AS
SELECT 
    COUNT(*) as total_entries,
    COUNT(hash) as entries_with_hash,
    COUNT(DISTINCT hash) as unique_hashes,
    MIN(ts) as oldest_entry,
    MAX(ts) as newest_entry,
    COUNT(*) FILTER (WHERE hash IS NOT NULL AND length(hash) = 64 AND hash ~ '^[a-f0-9]+$') as valid_hashes
FROM ledger.entries;

-- Grant appropriate permissions (adjust as needed for your setup)
-- GRANT SELECT ON ledger.entries TO rekor_anchoring_user;
-- GRANT SELECT ON ledger.anchoring_candidates TO rekor_anchoring_user;
-- GRANT EXECUTE ON FUNCTION ledger.get_anchoring_hashes(INTEGER) TO rekor_anchoring_user;

-- Example queries for the Rekor anchoring workflow:

-- Query 1: Get hashes for processing (what the workflow uses)
-- SELECT hash, ts FROM ledger.get_anchoring_hashes(1000);

-- Query 2: Check performance stats
-- SELECT * FROM ledger.anchoring_stats;

-- Query 3: Find specific hash (for debugging)
-- SELECT * FROM ledger.entries WHERE hash = 'your_hash_here';

-- Maintenance queries (run periodically):

-- Check index usage
-- SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch 
-- FROM pg_stat_user_indexes 
-- WHERE tablename = 'entries';

-- Analyze table statistics (run after bulk inserts)
-- ANALYZE ledger.entries;

-- Vacuum for maintenance (adjust as needed)
-- VACUUM ANALYZE ledger.entries;