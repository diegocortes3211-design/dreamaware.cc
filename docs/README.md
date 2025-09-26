# Rekor Anchoring System

This directory contains the implementation of a production-ready Rekor anchoring workflow that processes ledger hashes and anchors them to the [Rekor](https://docs.sigstore.dev/rekor/overview) transparency log for immutable auditability.

## 🎯 Quick Start

### Automatic Operation (Recommended)
The workflow runs automatically every day at 2:00 AM UTC with safe defaults - no action required.

### Manual Execution
```bash
# Standard run
gh workflow run rekor-anchor.yml

# Dry run for testing
gh workflow run rekor-anchor.yml --field dry_run=true --field batch_size=10

# Custom parameters
gh workflow run rekor-anchor.yml \
  --field N=2000 \
  --field batch_size=500 \
  --field rekor_server=https://rekor.sigstore.dev
```

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `.github/workflows/rekor-anchor.yml` | Main workflow implementation |
| `docs/rekor-anchoring-runbook.md` | Complete operational guide |
| `docs/database-schema.sql` | Database optimizations and schema |
| `test-rekor-workflow.sh` | Validation test suite |
| `validate-acceptance.sh` | Acceptance criteria checker |

## ✨ Key Features

### 🛡️ Security & Safety
- **Input Sanitization**: All parameters validated and sanitized
- **Safe Defaults**: Scheduled runs use conservative limits
- **Digest Pinning**: Exact Docker image digests captured and used
- **Audit Trail**: Complete artifact chain for forensic analysis

### ⚡ Performance & Reliability  
- **SQL-side Filtering**: Invalid hashes filtered at database level
- **Batch Processing**: Configurable batch sizes with safety caps
- **Jittered Retries**: Randomized delays prevent thundering herd
- **Database Indexes**: Optimized queries for large-scale processing

### 🔍 Observability
- **Rich Artifacts**: 8 different artifact types for debugging
- **Workflow Summaries**: Clear metrics and status reporting
- **Traceability**: Image digests and processing logs
- **Health Checks**: Built-in connectivity and validation tests

### 🎛️ Flexibility
- **Dual-flag Support**: Compatible with different Rekor CLI versions
- **Dry Run Mode**: Non-invasive auditing and testing
- **Server Override**: Support for staging/custom Rekor servers
- **Manual Control**: All parameters can be overridden when needed

## 🚀 Implementation Highlights

### Workflow Enhancements
- ✅ Safe parameter defaults with input sanitization
- ✅ SQL-side filtering and digest-pinned Docker runs
- ✅ Dual-flag Rekor CLI compatibility (`--sha256` and `--sha`)
- ✅ Jittered retries to avoid thundering herd issues
- ✅ Complete artifact generation (hashes.proc, image-digest.txt, etc.)
- ✅ Batch size limiter with safety caps

### Database Enhancements
- ✅ Optimized indexes (`idx_ledger_ts_desc`, `idx_ledger_hash`)
- ✅ Performance views and functions
- ✅ SQL-side hash validation and filtering

### Documentation & Operations
- ✅ Comprehensive runbook with examples
- ✅ Troubleshooting guides and best practices
- ✅ Health check procedures
- ✅ Complete parameter documentation

## 📊 Acceptance Criteria Status

All requirements from the original problem statement have been implemented and verified:

- ✅ Scheduled runs succeed with no inputs (defaults applied)
- ✅ Manual runs honor all inputs (N, dry_run, batch_size, rekor_server, rekorcliimage)
- ✅ Rekor CLI image is pulled, digest captured, and Docker commands use the digest
- ✅ Artifacts include all expected files (8 different artifact types)
- ✅ Workflow summary shows counts for considered, usable, anchored, skipped, and failed hashes

## 🏃‍♂️ Running Tests

```bash
# Test parameter validation and core logic
./test-rekor-workflow.sh

# Validate all acceptance criteria  
./validate-acceptance.sh
```

## 🔧 Database Setup

Apply the database optimizations for best performance:

```bash
# Apply schema enhancements (optional but recommended)
psql -f docs/database-schema.sql
```

## 📚 Further Reading

- **[Rekor Anchoring Runbook](docs/rekor-anchoring-runbook.md)** - Complete operational guide
- **[Database Schema](docs/database-schema.sql)** - Performance optimizations
- **[Sigstore Documentation](https://docs.sigstore.dev/)** - Learn more about Rekor and Sigstore

## 🔮 Future Enhancements

The system is designed to be extensible. Planned improvements include:

- **Cosign Verification** (Issue #10): Optional cosign verification of Rekor CLI image attestations
- **Advanced Filtering**: Subject-based and time-range filtering options
- **Enhanced Monitoring**: Prometheus metrics and Grafana dashboards

---

*This implementation follows security best practices and provides production-grade reliability, observability, and maintainability.*