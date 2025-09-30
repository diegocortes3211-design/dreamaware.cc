#!/bin/bash

# Deploy DreadAPI with maximum privacy
echo "🚀 Deploying DreadAPI with Tor/Monero-inspired privacy..."

# Create namespace
kubectl create namespace dreamaware-public --dry-run=client -o yaml | kubectl apply -f -

# Apply privacy-focused configuration
kubectl apply -f k8s/public/dreadapi-deployment.yaml

# Create network policies to enforce privacy
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dreadapi-deny-all
  namespace: dreamaware-public
spec:
  podSelector:
    matchLabels:
      app: dreadapi
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
EOF

echo "✅ DreadAPI deployed with maximum privacy settings"
echo "🔒 Features enabled:"
echo "   - Zero-knowledge sessions"
echo "   - Ring signatures (Monero-inspired)"
echo "   - Onion routing (Tor-inspired)"
echo "   - Forward secrecy"
echo "   - No PII collection"
echo "   - Immediate data deletion"

# Test deployment
echo "🧪 Testing deployment..."
kubectl -n dreamaware-public wait --for=condition=ready pod -l app=dreadapi --timeout=60s

if [ $? -eq 0 ]; then
    echo "✅ DreadAPI is ready and privacy-focused"
else
    echo "❌ Deployment check failed"
    exit 1
fi