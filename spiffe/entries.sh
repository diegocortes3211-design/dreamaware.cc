#!/usr/bin/env bash
set -euo pipefail

# Register SPIFFE IDs for services
spire-server entry create -socketPath /tmp/spire-server/private/api.sock \
  -spiffeID spiffe://dreamaware/agent/meta \
  -selector k8s:sa:meta-agent \
  -parentID spiffe://dreamaware/ns/default/sa/spire-agent