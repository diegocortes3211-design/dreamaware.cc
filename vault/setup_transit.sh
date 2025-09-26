#!/usr/bin/env bash
set -euo pipefail

: "${VAULT_ADDR:?} ${VAULT_TOKEN:?}"

vault secrets enable transit || true
vault write -f transit/keys/ledger-ed25519 type=ed25519 exportable=false allow_plaintext_backup=false
vault write transit/keys/ledger-ed25519/config min_decryption_version=1 min_encryption_version=1 deletion_allowed=false

# rotation (periodic)
# vault write -f transit/keys/ledger-ed25519/rotate