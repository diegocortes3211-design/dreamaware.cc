# Rekor Anchoring Workflow - Operator Runbook

## Overview

The "Ops — Rekor Anchor" workflow provides automated hash anchoring to the [Rekor transparency log](https://rekor.sigstore.dev/). This workflow ensures cryptographic hashes are properly validated, deduplicated, and anchored with appropriate retry mechanisms and comprehensive reporting.

## Workflow Inputs

### Required Parameters
- **N** (number): Number of hashes to process (default: 10)

### Optional Parameters  
- **rekor_server** (string): Rekor server URL (default: `https://rekor.sigstore.dev`)
- **rekor_cli_image** (string): Rekor CLI Docker image (default: `ghcr.io/sigstore/rekor-cli:v1.3.5`)
- **dry_run** (boolean): Perform a dry run without actual anchoring (default: false)

## Usage Examples

### Standard Execution
Manually dispatch the workflow with default parameters:
```
N: 10
rekor_server: https://rekor.sigstore.dev
rekor_cli_image: ghcr.io/sigstore/rekor-cli:v1.3.5
dry_run: false
```

### Custom Rekor Server
To use a custom Rekor server (e.g., for testing):
```
N: 5
rekor_server: https://rekor-test.sigstore.dev
rekor_cli_image: ghcr.io/sigstore/rekor-cli:v1.3.5
dry_run: false
```

### Different CLI Version
To use a specific Rekor CLI version:
```
N: 20
rekor_server: https://rekor.sigstore.dev
rekor_cli_image: ghcr.io/sigstore/rekor-cli:v1.3.6
dry_run: false
```

### Dry Run Mode
For testing workflow logic without actual anchoring:
```
N: 100
rekor_server: https://rekor.sigstore.dev
rekor_cli_image: ghcr.io/sigstore/rekor-cli:v1.3.5
dry_run: true
```

## Workflow Process

### 1. Hash Generation and Validation
- Generates or processes input hashes
- **Validates** that hashes are exactly 64-character hexadecimal strings
- **Deduplicates** identical hashes to prevent redundant operations
- Creates `hashes_raw.txt` and `hashes.txt` files

### 2. Rekor Processing
- Processes each validated hash through the Rekor CLI
- Implements **retry/backoff mechanism** for network-dependent operations:
  - Maximum 3 attempts per operation
  - Exponential backoff: 1s, 2s, 4s delays
- Categorizes hashes into three outcomes:
  - **Anchored**: Successfully submitted and anchored
  - **Skipped**: Already exists in Rekor transparency log  
  - **Failed**: Unable to anchor after retries

### 3. Artifact Generation
The workflow generates the following artifacts for operator review:

| Artifact | Purpose |
|----------|---------|
| `hashes_raw.txt` | Original input hashes before validation |
| `hashes.txt` | Validated and deduplicated hashes |
| `anchored.txt` | Hashes successfully anchored to Rekor |
| `skipped.txt` | Hashes already present in Rekor |  
| `failed.txt` | Hashes that failed to anchor after retries |

## Verification Steps

### Post-Workflow Verification
After workflow completion, verify results using the pinned Rekor CLI image:

```bash
# Download and examine anchored hashes
cat anchored.txt | head -5

# Spot-check a hash from anchored.txt
HASH="<hash-from-anchored.txt>"
docker run --rm ghcr.io/sigstore/rekor-cli:v1.3.5 search --sha256 $HASH --rekor-server https://rekor.sigstore.dev
```

### Expected Outputs
1. **Workflow Summary**: Detailed counts and categorization displayed in GitHub Actions summary
2. **Artifacts**: All five artifact files uploaded with 30-day retention
3. **Success Indicators**: 
   - Non-zero anchored count (unless all hashes already exist)
   - Reasonable success rate (failures should be investigated)
   - All valid hashes processed (considered count matches expectations)

## Troubleshooting

### Common Issues

#### High Failure Rate
**Symptoms**: Large number of hashes in `failed.txt`
**Investigation**: 
1. Check workflow logs for network timeout errors
2. Verify Rekor server accessibility: `curl -I <rekor_server>/api/v1/log`
3. Test with smaller batch size
4. Consider using dry run mode to test workflow logic

#### Hash Validation Failures  
**Symptoms**: Low "considered" count compared to raw input
**Investigation**:
1. Examine `hashes_raw.txt` for invalid entries
2. Verify input source generates proper SHA256 hashes
3. Check for encoding issues (spaces, newlines, case sensitivity)

#### Network Connectivity Issues
**Symptoms**: Retry attempts failing consistently  
**Investigation**:
1. Check GitHub Actions runner connectivity
2. Verify Rekor server status and accessibility
3. Review Docker image pull success
4. Consider increasing retry counts or delays

### Artifact Analysis

#### Review Failed Hashes
```bash
# Download failed.txt from workflow artifacts
cat failed.txt | while read hash; do
  echo "Investigating failed hash: $hash"
  # Manual verification steps
done
```

#### Validate Anchored Results
```bash
# Verify anchored hashes are actually in Rekor
cat anchored.txt | head -10 | while read hash; do
  docker run --rm ghcr.io/sigstore/rekor-cli:v1.3.5 search --sha256 $hash
done
```

## Security Considerations

- **Input Validation**: Only 64-character hex strings are processed
- **Rate Limiting**: Built-in delays prevent overwhelming Rekor servers
- **Retry Logic**: Prevents transient failures from causing permanent failures
- **Dry Run Mode**: Allows safe testing without side effects
- **Pinned Images**: Uses specific CLI version to ensure reproducible behavior

## Monitoring and Alerting

### Key Metrics to Monitor
- **Success Rate**: Anchored / (Anchored + Failed) should be > 90%
- **Processing Time**: Should scale linearly with input size
- **Network Failures**: Should be minimal with retry mechanism
- **Validation Rate**: Considered / Raw should be close to 100%

### Recommended Alerts
- Workflow failure (exit code != 0)
- Success rate below 80% 
- Processing time exceeding expected thresholds
- High number of network retry attempts

## Maintenance

### Regular Tasks
- **Weekly**: Review failure trends and investigate recurring issues
- **Monthly**: Verify Rekor CLI image updates and test compatibility
- **Quarterly**: Review and update retry/backoff parameters based on performance

### Version Updates
When updating the Rekor CLI version:
1. Test with dry run mode first
2. Verify CLI compatibility with current Rekor server
3. Update default image in workflow and documentation
4. Validate against known hash samples

---

*Last Updated: Generated for Rekor CLI v1.3.5*  
*Rekor Server: https://rekor.sigstore.dev*