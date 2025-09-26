# Ledger Service - Cryptographic Append-Only Log

Go service providing a cryptographically signed append-only ledger with Vault integration.

## Features

- **Ed25519 Signatures**: Uses HashiCorp Vault Transit for signing
- **Append-Only**: Immutable ledger entries with database constraints
- **CockroachDB**: Distributed SQL database for persistence
- **RESTful API**: Simple HTTP interface for appending entries
- **Cryptographic Integrity**: Every entry is signed and verifiable

## Development

```bash
# From repository root
npm run dev:ledger

# Or from this directory (with Go installed)
go run server.go
```

## Building

```bash
# Build binary
go build -o bin/server server.go

# Or via npm script
npm run build
```

## Configuration

- **Port**: 8088
- **Database**: CockroachDB (configurable via CRDB_DSN)
- **Vault**: HashiCorp Vault for Ed25519 signing
- **Technologies**: Go, pgx driver, Vault API

## Environment Variables

```bash
# CockroachDB connection
CRDB_DSN="postgresql://root@localhost:26257/ledger?sslmode=disable"

# Vault configuration (see Vault setup below)
VAULT_ADDR="http://localhost:8200"
VAULT_TOKEN="your-vault-token"
```

## API

### POST /append
Append a new signed entry to the ledger.

```bash
curl -X POST http://localhost:8088/append \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "user123",
    "payload": "SGVsbG8gV29ybGQ=",
    "meta": {"action": "login", "ip": "192.168.1.1"}
  }'
```

**Response**: HTTP 201 Created

## Database Schema

```sql
CREATE TABLE ledger.entries (
    id SERIAL PRIMARY KEY,
    subject STRING NOT NULL,
    payload BYTES NOT NULL,
    sig BYTES NOT NULL,
    pubkey STRING NOT NULL,
    meta JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Vault Setup

1. Start Vault dev server: `vault server -dev`
2. Enable Transit engine: `vault secrets enable transit`
3. Create Ed25519 key: `vault write -f transit/keys/ledger-sign type=ed25519`
4. Get signing token and configure environment

## Security

- All payloads are signed with Ed25519 private keys stored in Vault
- Database uses serializable transactions for consistency
- Signatures are verified before storage (implement verification endpoint)
- Payloads should be base64-encoded in JSON

## Extending

- Add payload verification endpoint
- Implement subject-based querying
- Add batch append operations
- Include merkle tree for additional integrity