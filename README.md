# Fortress v4 (Ledger + Proofs)

**What this is**: A reproducible, containerized evidence pack proving: quorum resilience (CockroachDB), key custody (Vault Transit, non-exportable), and public anchoring (Rekor + witness cosigns).

**Single command (local dev)**
```bash
docker compose up -d --build
```

### Smoke append
```bash
curl -XPOST localhost:8088/append -H 'content-type: application/json' \
-d '{"subject":"smoke","payload":"aGVsbG8="}'
```

---

### Canonical artifacts = CI outputs
- **Anchoring Proof** → GitHub Actions artifact `anchoring-proof`
- **Chaos Report** → artifact `chaos-report`
- **SnapSec Evidence** → artifact `snapsec-evidence`

---

### Ruthless verification (pulls CI artifacts)
Requires: `curl`, `unzip`. Uses a containerized verifier if Docker is present.
```bash
GITHUB_TOKEN=ghp_... REPO=owner/repo ./scripts/verify.sh anchoring-proof
```

See `docs/PROOFS_INDEX.md` for binder links.