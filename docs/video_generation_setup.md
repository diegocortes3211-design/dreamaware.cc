# Video Generation Service: Setup and Operations

This document contains the commands required to set up and operate the video generation service.

## Phase 1: Vault & Auth

```bash
# 0. namespaces used in this run
export NS_STG=dreamaware-staging
export NS_PROD=dreamaware

# 1) enable engines
vault secrets enable -path=video-gen kv-v2
vault secrets enable -path=transit transit

# 2) create a dedicated transit key for metadata
vault write -f transit/keys/video-metadata rotation_period=720h

# 3) load KV v2 secrets that match the client code
vault kv put video-gen/llm/openai        api_key="$(vault kv get -field=value secret/llm/openai)"
vault kv put video-gen/tts/azure         api_key="$(vault kv get -field=value secret/azure/tts)"
vault kv put video-gen/materials/pexels  keys='["key1","key2","key3"]'

# 4) least privilege policy for runtime
cat >/tmp/video-gen-service.hcl <<'EOF'
path "video-gen/data/llm/*"            { capabilities = ["read"] }
path "video-gen/data/tts/*"            { capabilities = ["read"] }
path "video-gen/data/materials/*"      { capabilities = ["read"] }
path "transit/encrypt/video-metadata"  { capabilities = ["update"] }
path "transit/decrypt/video-metadata"  { capabilities = ["update"] }
EOF
vault policy write video-gen-service /tmp/video-gen-service.hcl

# 5) k8s auth role in STAGING namespace
kubectl create namespace "$NS_STG" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$NS_STG" create serviceaccount video-gen-service --dry-run=client -o yaml | kubectl apply -f -

vault write auth/kubernetes/role/video-gen-service \
  bound_service_account_names=video-gen-service \
  bound_service_account_namespaces="$NS_STG" \
  policies=video-gen-service \
  ttl=1h
```

## Phase 2: Sanitizer Test

```bash
# Execute from repo root
python services/video-generation/test_sanitizer.py
```

## Phase 3: CockroachDB DDL

```bash
# Deploy DDL
psql "$COCKROACH_URL" -f services/video-generation/schema/video_jobs.sql

# RLS Smoke Test
psql "$COCKROACH_URL" -c "SET app.current_user_id = '00000000-0000-0000-0000-000000000000'; SELECT count(*) FROM videogen.jobs;"
```

## Phase 4: LLM Service Manifest

```bash
# Deploy service
kubectl apply -f k8s/video-gen/llm-service.yaml && kubectl -n dreamaware-staging rollout status deployment/llm-service
```

## Phase 5: Mission Control Backend Contract

These are the API endpoints the backend should implement.

**Metrics:** `GET /api/videogen/metrics`
```json
{
  "queue_depth": 7,
  "renders_per_hour": 42,
  "hourly_cost": 3.27,
  "success_rate": 98.1,
  "cost_history": [{"timestamp":"2025-09-29T14:00:00Z","cost_usd":0.12}]
}
```

**Jobs:** `GET /api/videogen/jobs?status=processing,queued`
```json
[
  {
    "job_id":"<uuid>",
    "topic":"AI tech trends 2025",
    "status":"processing",
    "estimated_cost_usd":0.0187,
    "created_at":"2025-09-29T14:27:02Z",
    "video_url":null
  }
]
```

**Reference SQL Queries:**
```sql
-- queue depth
SELECT count(*) FROM videogen.jobs WHERE status IN ('queued','processing');

-- success rate last 24h
SELECT 100.0 * sum(CASE WHEN status='completed' THEN 1 ELSE 0 END) / count(*)
FROM videogen.jobs
WHERE created_at >= now() - '24 hours'::interval;

-- renders per hour last hour
SELECT count(*) FROM videogen.jobs
WHERE status='completed' AND completed_at >= now() - '1 hour'::interval;

-- hourly cost last hour
SELECT coalesce(sum(actual_cost_usd),0) FROM videogen.jobs
WHERE completed_at >= now() - '1 hour'::interval;
```

## Health Checks

```bash
# Vault connectivity from pod
kubectl -n dreamaware-staging exec deploy/llm-service -- \
python - <<'PY'
from vault_secrets import VideoGenSecrets
s = VideoGenSecrets()
print("openai key present:", bool(s.get_llm_key('openai')))
print("pexels keys count:", len(s.get_material_keys('pexels')))
PY

# DB connectivity and RLS
psql "$COCKROACH_URL" -c "SET app.current_user_id = '00000000-0000-0000-0000-000000000000'; \
INSERT INTO videogen.jobs (user_id, topic, status) VALUES ('00000000-0000-0000-0000-000000000000','sanity','queued'); \
SELECT topic, status FROM videogen.jobs WHERE user_id = '00000000-0000-0000-0000-000000000000';"

# Sanitizer run
python services/video-generation/test_sanitizer.py
```

## mTLS Security Policy

```bash
# Deploy security policies
kubectl apply -f k8s/security/peer-authentication.yaml -f k8s/security/authorization-policy.yaml
```