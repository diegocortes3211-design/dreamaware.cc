#!/usr/bin/env bash
set -euo pipefail

OUT="docs/proofs/anchoring"
mkdir -p "$OUT"

# Compute Merkle-like hourly checkpoint root: SHA256 over ordered (id||sig)
SQL="SELECT encode(sha256(string_agg(id::string||encode(sig,'hex'), '' ORDER BY ts ASC)),'hex') AS root FROM ledger.entries WHERE ts >= now() - interval '1 hour';"
ROOT=$(cockroach sql --insecure --host=localhost:26257 --format=raw -e "$SQL" | tail -n1 | tr -d '[:space:]')

if [[ -z "$ROOT" ]]; then
  echo "no entries in last hour, skipping"
  exit 0
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
CHK="$OUT/checkpoint.${STAMP}.root"
echo -n "$ROOT" > "$CHK"

# Rekor upload (hashedrekord)
rekor-cli upload --artifact "$CHK" \
  --type hashedrekord \
  --rekor_server "${REKOR_URL:-https://rekor.sigstore.dev}" \
  | tee "$OUT/rekor_entry.txt"

# Optional: witness cosignatures
if [[ -n "${WITNESS1_KEY:-}" ]]; then
  COSIGN_EXPERIMENTAL=1 cosign sign-blob --key env://WITNESS1_KEY "$CHK" --output-signature "$OUT/w1.sig"
fi
if [[ -n "${WITNESS2_KEY:-}" ]]; then
  COSIGN_EXPERIMENTAL=1 cosign sign-blob --key env://WITNESS2_KEY "$CHK" --output-signature "$OUT/w2.sig"
fi