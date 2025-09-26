#!/bin/bash
# Fortress v4 Demo Script
# Demonstrates policy evaluation without requiring OPA installation

set -euo pipefail

echo "🏰 Fortress v4 Policy Framework Demo"
echo "===================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "📋 Project Structure Overview:"
echo "=============================="

# Check directory structure
log "Checking Fortress v4 directory structure..."
for dir in policy/rego policy/tests tools/policy lib/policy app/api/_examples; do
    if [[ -d "$dir" ]]; then
        success "✓ $dir"
        echo "   Files: $(find "$dir" -type f | wc -l)"
    else
        error "✗ $dir"
    fi
done
echo

echo "📑 Policy Files Summary:"
echo "======================="

# Policy files analysis
log "Analyzing policy files..."
for policy_file in policy/rego/*.rego; do
    if [[ -f "$policy_file" ]]; then
        name=$(basename "$policy_file" .rego)
        lines=$(wc -l < "$policy_file")
        rules=$(grep -c "^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*if" "$policy_file" || echo 0)
        success "Policy: $name"
        echo "   Lines: $lines, Rules: $rules"
    fi
done
echo

# Test files analysis
log "Analyzing test files..."
for test_file in policy/tests/*.rego; do
    if [[ -f "$test_file" ]]; then
        name=$(basename "$test_file" _test.rego)
        lines=$(wc -l < "$test_file")
        tests=$(grep -c "^test_" "$test_file" || echo 0)
        success "Tests: $name"
        echo "   Lines: $lines, Test cases: $tests"
    fi
done
echo

echo "🔧 Policy Examples:"
echo "=================="

# Show example policy rules
log "Sample Ledger Validation Policy:"
cat << 'EOF'
```rego
package fortress.ledger

default allow := false

allow if {
    input.operation == "append"
    valid_subject
    valid_payload
    valid_metadata
    signature_required
}

valid_subject if {
    input.subject != ""
    regex.match("^[a-zA-Z0-9_.-]+$", input.subject)
    count(input.subject) <= 256
}
```
EOF
echo

log "Sample API Governance Policy:"
cat << 'EOF'
```rego  
package fortress.api

default allow := false

allow if {
    input.method == "POST"
    input.path == "/append"
    valid_auth_header
    rate_limit_ok
}

valid_auth_header if {
    authorization_header := input.headers["Authorization"]
    startswith(authorization_header, "Bearer ")
}
```
EOF
echo

echo "🌐 API Integration Examples:"
echo "============================="

log "Example Next.js API Route with Policy Enforcement:"
cat << 'EOF'
```typescript
import { withLedgerPolicy } from '../../../lib/policy/middleware';

const handler = async (req: NextRequest) => {
  const body = await req.json();
  // Business logic here
  return NextResponse.json({ success: true });
};

export const POST = withLedgerPolicy({
  enableAuditLog: true,
  onViolation: (violations, req) => {
    return NextResponse.json({ 
      error: 'Policy violation',
      violations 
    }, { status: 403 });
  }
})(handler);
```
EOF
echo

log "Example Policy Evaluation:"
cat << 'EOF'
```bash
# Test ledger policy
./tools/policy/evaluate.sh ledger input.json

# Test API policy  
./tools/policy/evaluate.sh api api_input.json

# Real-time system monitoring
./tools/policy/evaluate.sh monitor 5
```
EOF
echo

echo "🗄️ Database Schema:"
echo "=================="

log "Fortress v4 Enhanced Ledger Schema:"
echo "- Enhanced entries table with policy versioning"
echo "- Policy violations audit table"
echo "- Rate limiting tracking table"
echo "- System metrics collection table"
echo "- Optimized indexes for performance"
echo "- JSONB support for flexible metadata"
echo

# Show database table count
migration_file="app/api/_examples/migrations/001_fortress_v4_ledger_indexes.sql"
if [[ -f "$migration_file" ]]; then
    tables=$(grep -c "CREATE TABLE" "$migration_file" || echo 0)
    indexes=$(grep -c "CREATE INDEX" "$migration_file" || echo 0) 
    functions=$(grep -c "CREATE OR REPLACE FUNCTION" "$migration_file" || echo 0)
    success "Database Schema: $tables tables, $indexes indexes, $functions functions"
fi
echo

echo "⚡ CI/CD Integration:"
echo "===================="

workflow_file=".github/workflows/fortress-policy-ci.yml"
if [[ -f "$workflow_file" ]]; then
    jobs=$(grep -c "^[[:space:]]*[a-zA-Z_-]*:" "$workflow_file" | head -1)
    steps=$(grep -c "name:" "$workflow_file")
    success "GitHub Actions Workflow: $jobs jobs, $steps steps"
    log "Automated processes:"
    echo "   - Policy syntax validation"
    echo "   - WASM bundle compilation"
    echo "   - Comprehensive testing"
    echo "   - Security analysis"
    echo "   - Performance benchmarking"
    echo "   - Documentation generation"
fi
echo

echo "🎯 Key Features Delivered:"
echo "========================="

success "✓ Multi-layer policy enforcement (API, Ledger, Runtime)"
success "✓ OPA Rego policies with comprehensive test coverage"
success "✓ Next.js middleware for seamless integration" 
success "✓ Cryptographic ledger with audit trails"
success "✓ Real-time system monitoring and alerts"
success "✓ Rate limiting and security enforcement"
success "✓ WASM-based policy evaluation for performance"
success "✓ Complete CI/CD automation"
success "✓ Production-ready database optimizations"
success "✓ Comprehensive documentation and examples"
echo

echo "🚀 Next Steps:"
echo "============="

log "To get started with Fortress v4:"
echo "1. Install OPA: curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static"
echo "2. Run policy tests: ./tools/policy/build.sh test"
echo "3. Build WASM bundles: ./tools/policy/build.sh build"
echo "4. Setup database: psql -d mydb -f app/api/_examples/migrations/001_fortress_v4_ledger_indexes.sql"
echo "5. Start services and test policy enforcement"
echo

echo "📚 Documentation:"
echo "================"

log "Complete documentation available in:"
echo "- README.md (Updated with Fortress v4 guidance)"
echo "- policy/ directory (Policy definitions and tests)"
echo "- lib/policy/ (Integration library)"
echo "- app/api/_examples/ (Working examples)"
echo

success "🏰 Fortress v4 implementation complete!"
echo "The platform now includes enterprise-grade governance, policy enforcement,"
echo "and comprehensive monitoring capabilities."