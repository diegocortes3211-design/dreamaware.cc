set -euo pipefail

echo "Verifying Rekor, OPA, CRDB, Vault"

IMG="dreamaware/llm-service:v1.0.0"
DIGEST="$(docker inspect --format='{{index .RepoDigests 0}}' "$IMG" | cut -d@ -f2)"

rekor-cli search --sha "$DIGEST" >/dev/null

curl -s -X POST http://opa.dreamaware-staging:8181/v1/data/dreamaware/videogen/egress/allow \
-H "Content-Type: application/json" \
-d '{"input":{"attributes":{"source":{"principal":"spiffe://dreamaware.ai/ns/dreamaware-staging/sa/llm-service"},"request":{"http":{"host":"api.openai.com","method":"POST","path":"/v1/chat/completions"}}}}}' \
| jq -e '.result == true' >/dev/null

psql "$COCKROACH_URL" -c "SET DATABASE = videogen; SET app.current_user_id = '00000000-0000-0000-0000-000000000000'; INSERT INTO jobs (user_id, topic, status, llm_provider) VALUES ('00000000-0000-0000-0000-000000000000','verification_test','queued','openai');"

curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
-X POST http://vault.vault.svc.cluster.local:8200/v1/transit/encrypt/video-metadata \
-d '{"plaintext":"dGVzdA=="}' | jq -e '.data.ciphertext' >/dev/null

echo "All checks passed"
