# DreamAware.cc - Fortress v4 Platform

This project demonstrates a credit-based WebSocket backpressure system with rolling cached snapshots, enhanced with **Fortress v4** - a comprehensive governance and policy enforcement framework. It provides a foundational real-time data stream architecture for high-performance applications with robust security, compliance, and runtime monitoring.

## 🏗️ Architecture Overview

DreamAware.cc combines real-time data streaming with enterprise-grade governance:

- **Real-time WebSocket streaming** with credit-based flow control
- **Fortress v4 policy engine** using Open Policy Agent (OPA) 
- **Cryptographic ledger** with Vault-based signing
- **Runtime security monitoring** and performance enforcement
- **Comprehensive audit trail** and policy violation tracking

## 📁 Project Structure

### Core Application
- `server/`: Node.js and TypeScript WebSocket server
  - Implements credit-based flow control
  - Utilizes a non-blocking rolling snapshot cache (500ms interval)
  - Simulates a stream of deltas
- `client/`: Vite and TypeScript web client
  - Connects to the WebSocket server
  - Implements client-side credit management and message draining
  - Provides a simple UI to visualize stream statistics and test backpressure

### Fortress v4 Components
- `policy/`: OPA Rego policies and tests
  - `rego/`: Policy definitions for ledger, API, and runtime governance
  - `tests/`: Comprehensive test suites for all policies
- `tools/policy/`: Policy build and evaluation tooling
  - `build.sh`: Policy compilation, testing, and WASM bundle generation
  - `evaluate.sh`: Runtime policy evaluation and system monitoring
- `lib/policy/`: Next.js policy enforcement library
  - `client.ts`: Policy client for WASM bundle evaluation
  - `middleware.ts`: API middleware for policy enforcement
- `services/ledger/`: Go-based cryptographic ledger service
  - `server.go`: Ledger append service with Vault integration
- `app/api/_examples/`: Example API routes with policy integration
  - `ledger/append/`: Ledger append endpoint with policy enforcement
  - `health/`: Health check with runtime policy monitoring
  - `migrations/`: Database schema optimizations for Fortress v4

## 🚀 Quickstart

### Prerequisites
- Node.js 20+ and npm
- Go 1.21+ (for ledger service)
- OPA (Open Policy Agent) for policy evaluation
- PostgreSQL (for ledger storage)
- HashiCorp Vault (for cryptographic signing)

### 1. Install OPA
```bash
# Install OPA for policy evaluation
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static
chmod 755 ./opa
sudo mv ./opa /usr/local/bin/
```

### 2. Build and Test Fortress v4 Policies
```bash
# Build and test all policies
./tools/policy/build.sh all

# Or run individual steps
./tools/policy/build.sh test      # Run policy tests
./tools/policy/build.sh build     # Build WASM bundles
./tools/policy/build.sh docs      # Generate documentation
```

### 3. Setup Database
```bash
# Create and setup the database
createdb dreamaware_ledger
psql -d dreamaware_ledger -f app/api/_examples/migrations/001_fortress_v4_ledger_indexes.sql
```

### 4. Start the Ledger Service
```bash
# Configure environment
export CRDB_DSN="postgresql://user:password@localhost:5432/dreamaware_ledger?sslmode=disable"
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="your-vault-token"

# Start the Go ledger service
cd services/ledger
go run server.go
# Runs on :8088
```

### 5. Start the WebSocket Server
```bash
cd server
npm install
npm run dev
# Runs on ws://localhost:8080/stream
```

### 6. Start the Client Application
```bash
cd client
npm install
npm run dev
# Open http://localhost:5173
```

## 🔐 Fortress v4 Usage Examples

### Policy Evaluation

#### Test Ledger Policies
```bash
# Create test data
cat > /tmp/ledger_test.json << EOF
{
  "operation": "append",
  "subject": "test-transaction",
  "payload": "dGVzdCBwYXlsb2Fk",
  "meta": {"source": "api"},
  "require_signature": true
}
EOF

# Evaluate policy
./tools/policy/evaluate.sh ledger /tmp/ledger_test.json
```

#### Test API Policies
```bash
# Create API test data
cat > /tmp/api_test.json << EOF
{
  "method": "POST",
  "path": "/append",
  "headers": {"Authorization": "Bearer valid-token"},
  "remote_addr": "192.168.1.100",
  "rate_limits": {"valid-token": 30}
}
EOF

# Evaluate policy
./tools/policy/evaluate.sh api /tmp/api_test.json
```

#### Runtime System Monitoring
```bash
# Start real-time monitoring (5 second intervals)
./tools/policy/evaluate.sh monitor 5
```

### API Integration Examples

#### Ledger Append with Policy Enforcement
```bash
# Valid request
curl -X POST http://localhost:3000/api/_examples/ledger/append \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "subject": "test-transaction",
    "payload": "dGVzdCBwYXlsb2Fk",
    "meta": {"source": "api", "version": "1.0"}
  }'

# Response: 201 Created with transaction ID
```

#### Health Check with Runtime Policies
```bash
# Check system health with policy evaluation
curl http://localhost:3000/api/_examples/health

# Response includes:
# - System metrics (CPU, memory, network)
# - Policy evaluation results
# - Security and performance alerts
```

### Next.js Policy Integration

#### Using Policy Middleware
```typescript
// In your Next.js API route
import { withApiPolicy } from '../../../lib/policy/middleware';

const handler = async (req: NextRequest) => {
  // Your business logic here
  return NextResponse.json({ success: true });
};

// Apply policy enforcement
export const POST = withApiPolicy({
  enableAuditLog: true,
  onViolation: (violations, req) => {
    return NextResponse.json({ 
      error: 'Policy violation',
      violations 
    }, { status: 403 });
  }
})(handler);
```

#### Client-Side Policy Evaluation
```typescript
import { evaluateLedgerPolicy } from '../lib/policy/client';

// Evaluate policy before making request
const policyResult = await evaluateLedgerPolicy({
  operation: 'append',
  subject: 'user-transaction',
  payload: btoa('transaction data'),
  meta: { userId: '12345' }
});

if (policyResult.allowed) {
  // Make API request
  await fetch('/api/ledger/append', { ... });
} else {
  console.error('Policy violations:', policyResult.violations);
}
```

## 📊 Monitoring and Observability

### Policy Metrics
- **Policy evaluation latency**: Sub-millisecond evaluation times
- **WASM bundle size**: Optimized bundles under 1MB
- **Policy violation rates**: Tracked per policy type and client
- **System resource usage**: Memory, CPU, network monitoring

### Security Features
- **Rate limiting**: Configurable per-client limits
- **Authentication**: Bearer token validation
- **CORS protection**: Configurable allowed origins
- **Request size limits**: Prevent oversized payloads
- **Audit logging**: Comprehensive request/response logging

### Performance Guardrails
- **Memory limits**: 512MB default, configurable growth rate monitoring
- **CPU thresholds**: 80% sustained usage alerts
- **Network limits**: 1000 connections, 100Mbps bandwidth caps
- **Database monitoring**: Connection pool and query performance

## 🔒 Security Architecture

Fortress v4 implements defense-in-depth with multiple policy layers:

1. **API Gateway Policies**: Request validation, authentication, rate limiting
2. **Business Logic Policies**: Domain-specific validation rules
3. **Runtime Security Policies**: Resource usage, security monitoring
4. **Audit Policies**: Compliance logging and violation tracking

All policies are:
- **Declarative**: Written in OPA Rego for clarity and maintainability
- **Testable**: Comprehensive test suites with >95% coverage
- **Versionable**: Policy versioning and backwards compatibility
- **Observable**: Detailed evaluation metrics and violation reporting

## 🚀 Deployment

### Production Checklist
- [ ] Deploy WASM policy bundles to CDN
- [ ] Configure Vault for cryptographic signing
- [ ] Setup PostgreSQL with proper indexing
- [ ] Enable audit logging and monitoring
- [ ] Configure rate limiting and security policies
- [ ] Test policy enforcement in staging environment
- [ ] Setup automated policy testing in CI/CD

### CI/CD Integration
The included GitHub Actions workflow (`fortress-policy-ci.yml`) provides:
- Automated policy testing and validation
- WASM bundle building and security scanning
- Performance benchmarking
- Integration testing with database
- Security analysis and documentation generation

---

## 🎯 Next Steps

This platform provides a robust foundation for enterprise applications requiring:
- **Real-time data streaming** with backpressure management
- **Policy-driven governance** with OPA integration
- **Cryptographic audit trails** with Vault signing
- **Comprehensive monitoring** and security enforcement

Future enhancements could include:
- Advanced graph data visualization
- Multi-tenant policy isolation
- Machine learning-based anomaly detection
- Integration with external identity providers
- Custom policy DSL for domain experts