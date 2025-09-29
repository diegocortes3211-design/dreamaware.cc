#!/bin/bash
set -euo pipefail

echo "Applying Istio mTLS and SPIFFE identities in staging..."
kubectl apply -f k8s/security/peer-authentication-staging.yaml
kubectl apply -f k8s/security/authz-videogen.yaml

echo "Deploying OPA EnvoyFilter for egress..."
kubectl apply -f k8s/security/envoyfilter-opa-egress.yaml

echo "Loading OPA policies..."
curl -X PUT http://opa.dreamaware-staging:8181/v1/policies/videogen-egress --data-binary @policies/videogen-egress.rego
curl -X PUT http://opa.dreamaware-staging:8181/v1/policies/videogen-input --data-binary @policies/videogen-input.rego

echo "Applying CockroachDB schema..."
psql "$COCKROACH_URL" -f cockroachdb/schema/videogen.sql

echo "Deploying llm-service in dreamaware-staging..."
kubectl apply -f k8s/video-gen/llm-service.yaml
kubectl -n dreamaware-staging rollout status deploy/llm-service

echo "Running verifier..."
bash scripts/verify_videogen.sh

echo "Deployment finished."
