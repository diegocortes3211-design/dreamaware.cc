# Rekor Anchoring Runbook

This runbook provides operational guidance for the Rekor anchoring workflow that processes ledger hashes and anchors them to the Rekor transparency log.

## Overview

The Rekor anchoring workflow automatically processes hashes from the ledger database and anchors them to Rekor for immutable transparency logging. It supports both scheduled automatic runs and manual execution with customizable parameters.

## Workflow Parameters

### Core Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `N` | Maximum number of hashes to process per run | `1000` | No |
| `batch_size` | Cap for processing per run (safety limit) | `500` | No |
| `dry_run` | Non-invasive audit mode (searches without uploads) | `false` | No |
| `rekor_server` | Rekor server URL override | `https://rekor.sigstore.dev` | No |
| `rekorcliimage` | Rekor CLI Docker image override | `gcr.io/projectsigstore/rekor-cli:latest` | No |

### Parameter Details

#### `dry_run` (boolean)
- **Purpose**: Enables audit mode that performs searches without actual uploads
- **When to use**: 
  - Testing workflow changes
  - Auditing existing anchored hashes
  - Verifying connectivity before live runs
- **Example**: `dry_run: true`

#### `batch_size` (integer)
- **Purpose**: Limits the number of hashes processed per workflow run
- **Safety**: Automatically capped at 1000 to prevent resource exhaustion
- **When to adjust**: 
  - Reduce for testing: `batch_size: 10`
  - Increase for catch-up: `batch_size: 1000`

#### `rekor_server` and `rekorcliimage`
- **Purpose**: Allow testing against different Rekor instances or CLI versions
- **Security**: URLs and image names are validated and sanitized
- **Use cases**:
  - Testing against staging Rekor: `rekor_server: https://rekor-staging.sigstore.dev`
  - Pinning CLI version: `rekorcliimage: gcr.io/projectsigstore/rekor-cli:v1.2.1`

## Usage Examples

### Manual Workflow Execution

#### Standard Production Run
```bash
gh workflow run rekor-anchor.yml
```

#### Dry Run Audit
```bash
gh workflow run rekor-anchor.yml \
  --field dry_run=true \
  --field batch_size=100
```

#### Custom Batch Processing
```bash
gh workflow run rekor-anchor.yml \
  --field N=2000 \
  --field batch_size=500 \
  --field dry_run=false
```

#### Testing with Custom Rekor Server
```bash
gh workflow run rekor-anchor.yml \
  --field rekor_server=https://rekor-staging.sigstore.dev \
  --field batch_size=10 \
  --field dry_run=true
```

### Rekor CLI Health Check

Use the Rekor CLI `loginfo` command to verify server health:

```bash
# Check main Rekor server
docker run --rm gcr.io/projectsigstore/rekor-cli:latest \
  rekor-cli loginfo --rekor_server https://rekor.sigstore.dev

# Check staging server  
docker run --rm gcr.io/projectsigstore/rekor-cli:latest \
  rekor-cli loginfo --rekor_server https://rekor-staging.sigstore.dev
```

Expected healthy output:
```
Verification Successful!
Active TreeSize: 47234567
Total TreeSize: 47234568
Root Hash: abcd1234...
```

### Image Digest Pinning

For reproducible runs, pin to the exact image digest used in a previous workflow:

```bash
# Find the digest from a previous run's image-digest.txt artifact
DIGEST="sha256:abcd1234567890..."

# Run with pinned digest
gh workflow run rekor-anchor.yml \
  --field rekorcliimage="gcr.io/projectsigstore/rekor-cli@${DIGEST}"
```

## Artifacts and Traceability

Each workflow run produces comprehensive artifacts for audit and debugging:

### Generated Artifacts

| Artifact | Description | Use Case |
|----------|-------------|----------|
| `hashes_raw.txt` | Raw hashes from database query | Debug SQL filtering |
| `hashes.txt` | Validated hashes ready for processing | Input verification |  
| `hashes.proc` | Post-batch-limit processed set | Batch size verification |
| `attempted.txt` | All hashes that were attempted | Full processing log |
| `anchored.txt` | Successfully anchored hashes | Success tracking |
| `skipped.txt` | Already anchored hashes (duplicates) | Deduplication log |
| `failed.txt` | Failed anchoring attempts | Error investigation |
| `image-digest.txt` | Exact Rekor CLI image digest used | Reproducibility |

### Workflow Summary

Each run generates a summary showing:
- Run configuration (mode, server, limits)  
- Processing results (considered, usable, anchored, skipped, failed counts)
- Traceability information (image digest, artifacts)

## Operations Notes

### Scheduled Runs
- **Frequency**: Daily at 2:00 AM UTC
- **Default behavior**: Safe parameters applied automatically
- **No input required**: Runs with sensible defaults

### Manual Runs  
- **Override capability**: All parameters can be customized
- **Input validation**: All inputs are sanitized for security
- **Flexibility**: Supports testing, catch-up, and emergency scenarios

### Monitoring and Alerts

Key metrics to monitor:
- **Success rate**: `anchored_count / (anchored_count + failed_count)`
- **Processing efficiency**: `usable_count / considered_count` 
- **Batch utilization**: `processed_count / batch_size`
- **Workflow duration**: Should complete within 60 minutes

Alert conditions:
- Failed workflow runs
- Success rate below 90%
- Processing efficiency below 80%
- Workflow timeout (60+ minutes)

### Troubleshooting

#### Common Issues

**No hashes found**
```
Check database connectivity and query in the workflow
Verify ledger.entries table has data with valid hashes
```

**Rekor server connectivity issues**  
```
Verify rekor_server parameter is correct
Check Rekor server status with loginfo command
Review network connectivity from runner
```

**High failure rate**
```
Check rekor-cli version compatibility
Verify payload format matches Rekor requirements  
Review failed.txt artifact for specific error patterns
```

**Workflow timeouts**
```
Reduce batch_size parameter
Check if Rekor server is experiencing high latency
Consider splitting large batches across multiple runs
```

### Security Considerations

- **Input sanitization**: All parameters are validated and sanitized
- **Image pinning**: Exact image digests captured for reproducibility
- **Audit trail**: Complete artifact chain for forensic analysis
- **Access control**: Workflow requires appropriate GitHub permissions

### Database Schema Requirements

The workflow expects the following database structure:

```sql
-- Ledger entries table
CREATE TABLE IF NOT EXISTS ledger.entries (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    payload BYTEA NOT NULL,
    hash VARCHAR(64), -- SHA256 hex string
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sig BYTEA,
    pubkey TEXT,
    meta JSONB
);

-- Recommended indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ledger_ts_desc 
    ON ledger.entries (ts DESC);
    
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ledger_hash 
    ON ledger.entries (hash) 
    WHERE hash IS NOT NULL;

-- Optional: Unique constraint if ingestion guarantees uniqueness
-- ALTER TABLE ledger.entries ADD CONSTRAINT unique_hash UNIQUE (hash);
```

## Future Enhancements

### Planned Improvements

1. **Cosign Verification** (Issue #10)
   - Add optional cosign verification step
   - Verify Rekor CLI image attestations before use
   - Enhanced supply chain security

2. **Advanced Filtering**
   - Subject-based filtering options
   - Time-range processing windows  
   - Priority-based hash selection

3. **Enhanced Monitoring**
   - Prometheus metrics export
   - Grafana dashboard integration
   - Real-time alerting

### Configuration Evolution

As the system scales, consider:
- Database connection pooling
- Parallel processing batches
- Regional Rekor server selection
- Custom retry strategies per hash type

---

For questions or issues with the Rekor anchoring workflow, consult the GitHub Actions logs and artifacts, or contact the infrastructure team.