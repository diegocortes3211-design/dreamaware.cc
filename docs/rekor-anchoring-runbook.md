# Rekor Anchoring Workflow Runbook

This document provides operational guidance for the Rekor anchoring workflow, which automatically anchors file hashes to Sigstore's Rekor transparency log for enhanced supply chain security and traceability.

## Overview

The Rekor anchoring workflow (`rekor-anchor.yml`) provides automated anchoring of repository file hashes to the Rekor transparency log. This creates an immutable record of file contents that can be used for:

- Supply chain verification
- File integrity validation
- Audit trail maintenance
- Compliance requirements

## Workflow Parameters

The workflow supports several configurable parameters:

### `verify_image` (boolean, default: false)
Enable cosign verification of the Rekor-CLI image to ensure it was built by a GitHub Action from the `sigstore` organization.

**When to enable:**
- Production environments
- Security-sensitive deployments
- Compliance requirements

**Example:**
```yaml
verify_image: true
```

### `capture_proofs` (boolean, default: false)
Store Rekor entry JSON files for newly-anchored hashes in the `entries/` directory. Each successfully anchored hash generates an inclusion proof file containing the complete Rekor entry data.

**When to enable:**
- When you need detailed audit trails
- For compliance documentation
- When building provenance chains

**Example:**
```yaml
capture_proofs: true
```

### `fail_on_failed` (boolean, default: false)
Fail the workflow if any hash uploads fail. This only applies in non-dry-run mode - dry runs never fail regardless of this setting.

**When to enable:**
- Critical deployments where all files must be anchored
- When failures should block subsequent processes
- For strict compliance requirements

**Example:**
```yaml
fail_on_failed: true
```

### `dry_run` (boolean, default: false)
Run the workflow in dry-run mode without actually anchoring hashes to Rekor. Useful for testing and validation.

**Example:**
```yaml
dry_run: true
```

## Usage Examples

### Basic Scheduled Run
The workflow runs automatically via cron schedule (daily at 02:00 UTC) with default parameters:
- `verify_image: false`
- `capture_proofs: false` 
- `fail_on_failed: false`
- `dry_run: false`

### Manual Run with Image Verification
To manually run with cosign verification enabled:

1. Go to Actions → Rekor Anchoring
2. Click "Run workflow"
3. Set parameters:
   - `verify_image: true`
   - Leave others as defaults

### Capturing Inclusion Proofs
To run with inclusion proof capture:

1. Go to Actions → Rekor Anchoring
2. Click "Run workflow" 
3. Set parameters:
   - `capture_proofs: true`
   - Optionally enable `verify_image: true` for additional security

### Production Run with All Security Features
For maximum security and traceability:

1. Go to Actions → Rekor Anchoring
2. Click "Run workflow"
3. Set parameters:
   - `verify_image: true`
   - `capture_proofs: true`
   - `fail_on_failed: true`

### Testing with Dry Run
To test the workflow without actual anchoring:

1. Go to Actions → Rekor Anchoring
2. Click "Run workflow"
3. Set parameters:
   - `dry_run: true`
   - Configure other parameters as needed

## Artifacts and Outputs

### Generated Files

The workflow creates several output files:

- `hashes/hashes_raw.txt`: Raw SHA256 output with filenames
- `hashes/hashes.txt`: Clean list of hash values only
- `hashes/success_count.txt`: Number of successful anchors
- `hashes/failure_count.txt`: Number of failed anchors
- `artifact_summary.txt`: Summary of the run

### Inclusion Proofs (`entries/` directory)

When `capture_proofs` is enabled, the workflow creates an `entries/` directory containing:

- Individual JSON files named `{uuid}.json` for each successfully anchored hash
- Each file contains the complete Rekor entry data including:
  - Entry UUID
  - Timestamp
  - Hash value
  - Signature information
  - Merkle tree proof

**Example entry structure:**
```json
{
  "uuid": "24296fb24b8ad77af...",
  "attestation": {
    "data": "eyJoYXNoIjp7InNl...",
    "signature": "MEUCIQDx..."
  },
  "body": {
    "HashedRekordObj": {
      "data": {
        "hash": {
          "algorithm": "sha256",
          "value": "abc123..."
        }
      }
    }
  }
}
```

### Artifacts Upload

All generated files are uploaded as workflow artifacts with:
- **Name**: `rekor-anchoring-results-{run_number}`
- **Retention**: 90 days
- **Contents**: 
  - `hashes/` directory with all hash files
  - `entries/` directory (if `capture_proofs` enabled)
  - `artifact_summary.txt`

## Ops Notes

### Monitoring and Alerts

Monitor the following aspects of the workflow:

1. **Success Rate**: Track the ratio of successful vs failed anchors
2. **Execution Time**: Monitor workflow duration for performance issues
3. **Artifact Size**: Watch for growth in inclusion proof storage when `capture_proofs` is enabled
4. **Rate Limiting**: Be aware of Rekor API rate limits during high-volume operations

### Troubleshooting

#### Common Issues

**Image Verification Failures**
- Check if Rekor-CLI image is properly signed by sigstore organization
- Verify network connectivity to container registry
- Ensure cosign is properly installed

**Anchor Failures**
- Check Rekor service status: https://status.sigstore.dev/
- Verify network connectivity to rekor.sigstore.dev
- Review rate limiting policies

**High Failure Rates**
- May indicate Rekor service issues
- Check file integrity (corrupted files can cause failures)
- Review network connectivity and timeouts

#### Debugging Steps

1. **Check workflow logs** for detailed error messages
2. **Download artifacts** to examine failed hashes
3. **Run with dry_run: true** to test without anchoring
4. **Enable capture_proofs** to get detailed entry information
5. **Check Rekor status page** for service availability

### Performance Considerations

- **Hash Generation**: Time increases with repository size
- **Network I/O**: Each hash requires a separate API call to Rekor
- **Rate Limiting**: Workflow includes 1-second delays between uploads
- **Artifact Storage**: Inclusion proofs can generate significant artifact data

### Security Considerations

- **Image Verification**: Always enable in production environments
- **Inclusion Proofs**: Provide cryptographic evidence of anchoring
- **Artifact Retention**: Consider regulatory requirements for retention periods
- **Network Security**: All communication uses HTTPS

### Compliance and Audit

The workflow supports compliance requirements through:

- **Immutable Records**: Rekor provides tamper-evident logging
- **Cryptographic Proofs**: Inclusion proofs verify anchoring
- **Audit Trails**: Complete workflow logs and artifacts
- **Traceability**: Links file hashes to transparency log entries

### Capacity Planning

Estimate resource usage based on:
- Repository size (number of files)
- Frequency of runs
- Inclusion proof storage requirements
- Network bandwidth for API calls

For large repositories (>1000 files), consider:
- Breaking into batches
- Running less frequently
- Monitoring rate limits
- Optimizing artifact retention policies

## Emergency Procedures

### Workflow Failures

1. **Check Rekor service status** first
2. **Review workflow logs** for specific errors
3. **Download and examine artifacts** for failed hashes
4. **Re-run with dry_run** to validate configuration
5. **Contact repository maintainers** if persistent issues

### Service Outages

If Rekor service is unavailable:
1. **Monitor status page**: https://status.sigstore.dev/
2. **Defer non-critical runs** until service restoration
3. **Consider manual anchoring** for critical files if needed
4. **Review and update monitoring** to catch future outages

### Data Recovery

Inclusion proof data can be recovered by:
1. **Querying Rekor directly** using entry UUIDs
2. **Using rekor-cli get** command with known UUIDs  
3. **Extracting from workflow artifacts** if available
4. **Regenerating from hash values** if original proofs lost

---

**Last Updated**: December 2024  
**Workflow Version**: 1.0  
**Maintainer**: Infrastructure Team