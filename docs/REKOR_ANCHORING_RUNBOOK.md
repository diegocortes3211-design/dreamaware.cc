# Rekor Anchoring Workflow Runbook

This runbook describes the implementation, operation, and troubleshooting procedures for the DreamAware Ledger Service Rekor anchoring workflow.

## Overview

The DreamAware Ledger Service integrates with [Sigstore's Rekor](https://github.com/sigstore/rekor) transparency log to provide immutable, verifiable anchoring of ledger entries. This ensures cryptographic proof of existence and integrity for all signed ledger entries.

### Architecture Components

1. **Ledger Service** - Go service that signs and stores ledger entries
2. **Vault Transit** - Provides Ed25519 signing capabilities
3. **Rekor Integration** - Submits signed entries to transparency log
4. **GitHub Actions** - Automated CI/CD with security hardening
5. **PostgreSQL/CockroachDB** - Persistent storage with Rekor metadata

## Workflow Process

### 1. Entry Creation Flow

```mermaid
sequenceDiagram
    participant Client
    participant Ledger as Ledger Service
    participant Vault as HashiCorp Vault
    participant DB as Database
    participant Rekor as Rekor Log

    Client->>Ledger: POST /append {subject, payload}
    Ledger->>Vault: Sign payload with Ed25519
    Vault-->>Ledger: signature + public key
    Ledger->>DB: Store entry with signature
    DB-->>Ledger: entry_id
    Ledger-->>Client: HTTP 201 + entry details
    Ledger->>Rekor: Submit entry (async)
    Rekor-->>Ledger: log_id + index
    Ledger->>DB: Update with Rekor metadata
```

### 2. CI/CD Security Pipeline

The GitHub Actions workflow implements multiple security layers:

1. **Security Scanning**: Vulnerability and code analysis
2. **Container Signing**: Sigstore/cosign keyless signing
3. **SLSA Provenance**: Supply chain attestation
4. **Rekor Anchoring**: Transparency log submission
5. **Verification**: End-to-end validation

## Configuration

### Environment Variables

#### Required - Vault Configuration
```bash
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=hvs.ABCDEF...
VAULT_TRANSIT_KEY=ledger-ed25519
```

#### Required - Database Configuration
```bash
CRDB_DSN=postgresql://user:pass@localhost:26257/ledger?sslmode=require
```

#### Optional - Rekor Configuration
```bash
REKOR_SERVER_URL=https://rekor.sigstore.dev  # Default: public Rekor
```

### Database Schema

```sql
CREATE SCHEMA IF NOT EXISTS ledger;
CREATE TABLE ledger.entries (
    id SERIAL PRIMARY KEY,
    subject TEXT NOT NULL,
    payload_hash TEXT NOT NULL,       -- SHA256 hash (no sensitive data stored)
    sig TEXT NOT NULL,                -- Base64 Ed25519 signature
    pubkey TEXT NOT NULL,             -- Base64 public key
    meta JSONB DEFAULT '{}',          -- Additional metadata
    rekor_log_id TEXT DEFAULT '',     -- Rekor entry UUID
    rekor_index BIGINT DEFAULT 0,     -- Rekor log index
    created_at TIMESTAMP DEFAULT NOW(),
    anchored_at TIMESTAMP NULL        -- When Rekor anchoring completed
);

-- Indexes for performance
CREATE INDEX idx_entries_subject ON ledger.entries(subject);
CREATE INDEX idx_entries_created ON ledger.entries(created_at);
CREATE INDEX idx_entries_rekor ON ledger.entries(rekor_log_id) WHERE rekor_log_id != '';
```

## API Endpoints

### POST /append
Create and anchor a new ledger entry.

**Request:**
```json
{
  "subject": "user-action",
  "payload": "SGVsbG8gV29ybGQ=",  // base64-encoded data
  "meta": {
    "user_id": "12345",
    "action": "document_signed"
  }
}
```

**Response (201 Created):**
```json
{
  "id": 42,
  "subject": "user-action",
  "payload_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "signature": "base64-signature",
  "public_key": "base64-pubkey",
  "created_at": "2024-01-15T10:30:00Z",
  "rekor_log_id": "",  // Populated asynchronously
  "rekor_index": 0     // Populated asynchronously
}
```

### GET /entries
List recent ledger entries with Rekor status.

### GET /health
Service health check including Rekor connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "ok",
  "rekor": true
}
```

## Security Hardening Measures

### 1. Input Validation
- Subject and payload required
- Payload size limits enforced
- JSON schema validation for meta fields

### 2. Cryptographic Security
- Ed25519 signatures via Vault Transit
- Local signature verification before storage
- SHA256 hashing for payload storage (no sensitive data persisted)

### 3. Timeouts and Rate Limiting
- Vault requests: 10 second timeout
- Database operations: 15 second timeout  
- Rekor submissions: 30 second timeout
- HTTP client connection pooling with limits

### 4. Error Handling
- Graceful degradation if Rekor unavailable
- Async anchoring prevents blocking responses
- Comprehensive error logging and monitoring

### 5. Database Security
- Serializable isolation level for transactions
- Prepared statements prevent SQL injection
- Connection encryption required (sslmode=require)

## Operations

### Starting the Service

```bash
# Production
./ledger

# Development with logging
RUST_LOG=debug ./ledger
```

### Monitoring

Key metrics to monitor:
- Entry creation rate
- Vault signing latency
- Rekor anchoring success rate
- Database connection health
- Error rates by endpoint

### Log Analysis

Important log patterns:
```bash
# Successful entry creation
grep "Entry.*anchored to Rekor" /var/log/ledger.log

# Rekor failures (investigate immediately)
grep "Rekor anchoring failed" /var/log/ledger.log

# Vault issues
grep "vault sign:" /var/log/ledger.log
```

## Troubleshooting

### Common Issues

#### 1. Rekor Anchoring Failures

**Symptoms:**
- Entries created but `rekor_log_id` remains empty
- "Rekor anchoring failed" in logs

**Diagnosis:**
```bash
# Check Rekor connectivity
curl -s https://rekor.sigstore.dev/api/v1/log | jq .

# Test entry submission
rekor-cli upload --artifact test.txt
```

**Resolution:**
1. Verify REKOR_SERVER_URL configuration
2. Check network connectivity to Rekor
3. Validate entry format (hashedrekord schema)
4. Review Rekor service status

#### 2. Vault Signing Issues

**Symptoms:**
- "vault sign:" errors in logs
- 500 responses from /append endpoint

**Diagnosis:**
```bash
# Test Vault connectivity
curl -H "X-Vault-Token: $VAULT_TOKEN" \
     "$VAULT_ADDR/v1/transit/keys/$VAULT_TRANSIT_KEY"
```

**Resolution:**
1. Check Vault token validity and permissions
2. Verify transit key exists and is enabled
3. Ensure network connectivity to Vault
4. Review Vault audit logs

#### 3. Database Connection Issues

**Symptoms:**
- "database unhealthy" in health checks
- Connection timeouts

**Resolution:**
1. Verify database credentials and connection string
2. Check database server status
3. Review connection pool settings
4. Validate SSL/TLS configuration

### Emergency Procedures

#### Service Recovery
1. Check service health: `GET /health`
2. Review recent logs for errors
3. Verify environment variables
4. Restart service if necessary
5. Monitor entry creation after restart

#### Data Integrity Verification
```bash
# Verify recent entries have Rekor anchoring
psql $CRDB_DSN -c "
SELECT id, subject, rekor_log_id, anchored_at 
FROM ledger.entries 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY id DESC;
"

# Check for unanchored entries
psql $CRDB_DSN -c "
SELECT COUNT(*) as unanchored_count
FROM ledger.entries 
WHERE rekor_log_id = '' OR rekor_log_id IS NULL;
"
```

#### Manual Rekor Verification
```bash
# Verify a specific Rekor entry
rekor-cli get --uuid <rekor_log_id> --format json

# Search for entries by hash
rekor-cli search --sha <payload_hash>
```

## Verification Procedures

### End-to-End Verification

1. **Create Test Entry**
```bash
curl -X POST http://localhost:8088/append \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "test",
    "payload": "SGVsbG8gV29ybGQ=",
    "meta": {"test": true}
  }'
```

2. **Verify Signature**
```bash
# Extract signature and verify locally
echo "<base64-signature>" | base64 -d > signature.bin
echo "<base64-pubkey>" | base64 -d > pubkey.bin
echo "Hello World" | openssl dgst -verify pubkey.bin -signature signature.bin -sha256
```

3. **Verify Rekor Entry**
```bash
rekor-cli get --uuid <rekor_log_id> --format json
rekor-cli verify --artifact original-data.txt --format json
```

### Container Verification

```bash
# Verify container signature
cosign verify --certificate-identity-regexp=".*@users.noreply.github.com" \
              --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
              ghcr.io/diegocortes3211-design/dreamaware.cc/ledger:main

# Verify SLSA provenance
cosign verify-attestation --type slsaprovenance \
                         --certificate-identity-regexp=".*@users.noreply.github.com" \
                         --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
                         ghcr.io/diegocortes3211-design/dreamaware.cc/ledger:main
```

## Compliance and Auditing

### Audit Trail
Every ledger entry provides:
- Cryptographic signature (Ed25519)
- Timestamp of creation
- Rekor transparency log entry
- Immutable hash of original data

### Compliance Features
- **Non-repudiation**: Ed25519 signatures prevent denial
- **Integrity**: SHA256 hashes detect tampering  
- **Transparency**: Rekor provides public verifiability
- **Auditability**: Complete event trail in database

### Retention Policy
- Ledger entries: Retained indefinitely
- Rekor entries: Immutable public record
- Database backups: Follow organizational policy
- Log files: 90 day retention recommended

## Security Contacts

For security issues:
1. **Critical vulnerabilities**: Create private security advisory
2. **Operational issues**: Standard issue tracking
3. **Rekor/Sigstore issues**: Report to sigstore-security@googlegroups.com

## References

- [Sigstore Documentation](https://docs.sigstore.dev/)
- [Rekor API Reference](https://github.com/sigstore/rekor/blob/main/openapi.yaml)
- [SLSA Framework](https://slsa.dev/)
- [Ed25519 Specification](https://tools.ietf.org/html/rfc8032)
- [HashiCorp Vault Transit Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/transit)

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Review Schedule**: Quarterly