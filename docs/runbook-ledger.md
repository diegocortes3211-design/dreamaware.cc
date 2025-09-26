# Ledger Hash Rekor Anchoring - Operator Runbook

This runbook covers the automated workflow for anchoring ledger hashes to the Rekor transparency log, providing operators with the knowledge needed to monitor, trigger, and troubleshoot the process.

## Overview

The Rekor anchoring system automatically queries recent ledger entries from the database, computes SHA256 hashes of their payloads, and anchors these hashes to the [Rekor transparency log](https://rekor.sigstore.dev/). This provides cryptographic evidence and timestamping for ledger entries.

### Key Features

- **Automated Operation**: Runs hourly at `:17` UTC via GitHub Actions
- **Manual Trigger**: Supports on-demand execution with configurable parameters
- **Idempotent Design**: Safe to run multiple times; skips already-anchored hashes
- **Direct Hash Anchoring**: Uses `--sha256` flag for efficient anchoring without temporary files
- **Comprehensive Logging**: Provides detailed summaries and error reporting

## Prerequisites

### Required Secrets

The workflow requires the following GitHub repository secret:

- **`DATABASE_URL`**: PostgreSQL connection string for the ledger database
  - Format: `postgresql://username:password@host:port/database`
  - Example: `postgresql://user:pass@ledger.example.com:5432/ledger?sslmode=require`

### Verify Secret Configuration

Check that the secret is configured:

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Verify `DATABASE_URL` is listed under Repository secrets

## Workflow Triggers

### Scheduled Execution

The workflow runs automatically every hour at `:17` UTC:
- 00:17, 01:17, 02:17, etc.
- Processes up to 100 recent hashes per run
- No manual intervention required

### Manual Execution

To trigger the workflow manually:

1. **Via GitHub UI**:
   - Go to Actions tab in your repository
   - Select "Rekor Ledger Hash Anchoring" workflow
   - Click "Run workflow"
   - Optionally specify number of hashes to process (default: 50)

2. **Via GitHub CLI**:
   ```bash
   # Process default 50 hashes
   gh workflow run rekor-anchor.yml
   
   # Process specific number of hashes
   gh workflow run rekor-anchor.yml -f hash_limit=100
   ```

3. **Via REST API**:
   ```bash
   curl -X POST \
     -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/OWNER/REPO/actions/workflows/rekor-anchor.yml/dispatches \
     -d '{"ref":"main","inputs":{"hash_limit":"75"}}'
   ```

## Manual Verification

### Local Verification with Docker

You can verify anchored hashes locally using the same Dockerized Rekor CLI that the workflow uses:

```bash
# Pull the Rekor CLI image
docker pull gcr.io/projectsigstore/rekor-cli:latest

# Create a wrapper script (optional, for convenience)
cat > rekor-cli << 'EOF'
#!/bin/bash
docker run --rm -i gcr.io/projectsigstore/rekor-cli:latest "$@"
EOF
chmod +x rekor-cli

# Search for a specific hash
./rekor-cli search --sha256 <HASH_VALUE>

# Get detailed information about an entry
./rekor-cli search --sha256 <HASH_VALUE> --format json

# Verify an entry by UUID
./rekor-cli verify --uuid <UUID_FROM_SEARCH>
```

### Database Query for Recent Hashes

To see what hashes are being processed, query the database directly:

```sql
-- Get recent 10 hashes with metadata
SELECT 
    encode(sha256(payload), 'hex') as hash,
    subject,
    length(payload) as payload_size,
    created_at
FROM ledger.entries 
ORDER BY id DESC 
LIMIT 10;

-- Count total entries
SELECT COUNT(*) FROM ledger.entries;

-- Get entries from last 24 hours
SELECT 
    encode(sha256(payload), 'hex') as hash,
    subject
FROM ledger.entries 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### Check Rekor Public Instance

You can also search the public Rekor instance via web interface:
- Visit: https://search.sigstore.dev/
- Search by SHA256 hash
- View transparency log entries

## Monitoring and Observability

### Workflow Status

Monitor workflow executions:

1. **GitHub Actions Dashboard**:
   - Go to Actions tab
   - Check recent runs of "Rekor Ledger Hash Anchoring"
   - Review success/failure status and logs

2. **Workflow Badges** (add to README):
   ```markdown
   ![Rekor Anchoring](https://github.com/OWNER/REPO/workflows/Rekor%20Ledger%20Hash%20Anchoring/badge.svg)
   ```

### Log Analysis

Key log sections to monitor:

- **Hash Query**: Confirms database connectivity and hash retrieval
- **Anchoring Summary**: Shows counts of processed/anchored/skipped hashes
- **Verification**: Spot-checks successful anchoring

### Expected Log Output

Successful run example:
```
Querying recent ledger entries...
Found 25 hashes to process
Starting hash anchoring process...
Processing hash: abc123def456... (subject: user-action, size: 156 bytes)
  → anchoring: abc123def456...
  → successfully anchored: abc123def456...
Processing hash: 789xyz012... (subject: system-event, size: 203 bytes)  
  → already anchored: 789xyz012...

=== ANCHORING SUMMARY ===
Considered: 25
Anchored: 20
Skipped (already present): 5
Errors: 0

Hash anchoring completed successfully!
```

## Troubleshooting

### Common Issues

#### 1. DATABASE_URL Secret Missing

**Symptoms**:
```
ERROR: DATABASE_URL secret is not configured
```

**Solution**:
- Verify the `DATABASE_URL` secret is configured in repository settings
- Check the secret name matches exactly (case-sensitive)
- Ensure the secret has the correct PostgreSQL connection string format

#### 2. Database Connection Failures

**Symptoms**:
```
psql: error: connection to server failed
```

**Solution**:
- Verify database is accessible from GitHub Actions runners
- Check connection string format and credentials
- Ensure database allows connections from GitHub's IP ranges
- Test connection string locally if possible

#### 3. No Hashes Found

**Symptoms**:
```
No hashes found in ledger
Found 0 hashes to process
```

**Solutions**:
- Check if ledger database has entries: `SELECT COUNT(*) FROM ledger.entries;`
- Verify table name and column names match the query
- Check if entries were created recently

#### 4. Rekor Anchoring Failures

**Symptoms**:
```
failed to anchor: <hash>
Some hashes failed to anchor
```

**Solutions**:
- Check Rekor service status: https://status.sigstore.dev/
- Verify hash format is correct (64-character hex string)
- Rate limiting: The workflow includes delays, but high volumes may need adjustment
- Try manual verification of a specific hash

#### 5. Permission Issues

**Symptoms**:
```
Error: Resource not accessible by integration
```

**Solutions**:
- Verify workflow permissions in `.github/workflows/rekor-anchor.yml`
- Check repository settings for Actions permissions
- Ensure secrets are accessible to the workflow

### Manual Recovery

If automated anchoring fails, you can manually anchor specific hashes:

```bash
# Get the hash from database
psql "$DATABASE_URL" -t -A -c "SELECT encode(sha256(payload), 'hex') FROM ledger.entries WHERE subject='specific-entry';"

# Manually anchor using Docker
docker run --rm gcr.io/projectsigstore/rekor-cli:latest upload --sha256 <HASH_VALUE> --type hashedrekord

# Verify anchoring
docker run --rm gcr.io/projectsigstore/rekor-cli:latest search --sha256 <HASH_VALUE>
```

### Getting Help

1. **Check Recent Workflow Runs**: Review logs in GitHub Actions for specific error details
2. **Rekor Documentation**: https://docs.sigstore.dev/rekor/overview/
3. **Database Logs**: Check ledger service logs for database issues
4. **Test Components**: Use the manual verification steps to isolate issues

## Security Considerations

- The workflow only reads from the database (no write operations)
- Hashes are computed from payload data, not raw sensitive information
- Rekor CLI runs in Docker container for isolation
- All operations are logged for audit purposes
- No sensitive data is exposed in logs (only hash values)

## Maintenance

### Regular Tasks

- Monitor workflow success rates
- Review anchoring summary reports
- Check for any persistent failures
- Verify database connectivity periodically

### Updates

When updating the workflow:
1. Test changes in a fork or development environment first
2. Monitor initial runs closely after deployment
3. Keep the runbook updated with any procedural changes

---

**Last Updated**: Initial version
**Workflow Version**: 1.0