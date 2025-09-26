#!/bin/bash
# Fortress v4 Policy Evaluation Script
# Real-time policy evaluation for runtime monitoring

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
POLICY_BUNDLES_DIR="${PROJECT_ROOT}/dist/policy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Evaluate ledger policy
evaluate_ledger_policy() {
    local input_file="$1"
    local policy_type="ledger"
    
    if [[ ! -f "$POLICY_BUNDLES_DIR/${policy_type}.wasm" ]]; then
        error "Policy bundle not found: ${POLICY_BUNDLES_DIR}/${policy_type}.wasm"
        error "Run 'tools/policy/build.sh build' first"
        return 1
    fi
    
    log "Evaluating ledger policy with input: $input_file"
    
    # Use OPA to evaluate the policy
    local result=$(opa eval -d "$POLICY_BUNDLES_DIR/${policy_type}.wasm" -i "$input_file" "data.fortress.ledger.allow")
    
    if echo "$result" | jq -e '.result[0].expressions[0].value == true' > /dev/null; then
        success "Ledger policy: ALLOW"
        return 0
    else
        warn "Ledger policy: DENY"
        
        # Get violation details
        local violations=$(opa eval -d "$POLICY_BUNDLES_DIR/${policy_type}.wasm" -i "$input_file" "data.fortress.ledger.violation")
        if [[ -n "$violations" ]]; then
            echo "Violations:"
            echo "$violations" | jq -r '.result[0].expressions[0].value[]? // empty'
        fi
        return 1
    fi
}

# Evaluate API policy
evaluate_api_policy() {
    local input_file="$1"
    local policy_type="api"
    
    if [[ ! -f "$POLICY_BUNDLES_DIR/${policy_type}.wasm" ]]; then
        error "Policy bundle not found: ${POLICY_BUNDLES_DIR}/${policy_type}.wasm"
        return 1
    fi
    
    log "Evaluating API policy with input: $input_file"
    
    local result=$(opa eval -d "$POLICY_BUNDLES_DIR/${policy_type}.wasm" -i "$input_file" "data.fortress.api.allow")
    
    if echo "$result" | jq -e '.result[0].expressions[0].value == true' > /dev/null; then
        success "API policy: ALLOW"
        return 0
    else
        warn "API policy: DENY"
        
        local violations=$(opa eval -d "$POLICY_BUNDLES_DIR/${policy_type}.wasm" -i "$input_file" "data.fortress.api.violation")
        if [[ -n "$violations" ]]; then
            echo "Violations:"
            echo "$violations" | jq -r '.result[0].expressions[0].value[]? // empty'
        fi
        return 1
    fi
}

# Evaluate runtime policy
evaluate_runtime_policy() {
    local input_file="$1"
    local policy_type="runtime"
    
    if [[ ! -f "$POLICY_BUNDLES_DIR/${policy_type}.wasm" ]]; then
        error "Policy bundle not found: ${POLICY_BUNDLES_DIR}/${policy_type}.wasm"
        return 1
    fi
    
    log "Evaluating runtime policy with input: $input_file"
    
    local result=$(opa eval -d "$POLICY_BUNDLES_DIR/${policy_type}.wasm" -i "$input_file" "data.fortress.runtime.allow")
    
    if echo "$result" | jq -e '.result[0].expressions[0].value == true' > /dev/null; then
        success "Runtime policy: ALLOW"
    else
        warn "Runtime policy: DENY"
    fi
    
    # Always check for alerts regardless of allow/deny
    local security_alerts=$(opa eval -d "$POLICY_BUNDLES_DIR/${policy_type}.wasm" -i "$input_file" "data.fortress.runtime.security_alert")
    local performance_alerts=$(opa eval -d "$POLICY_BUNDLES_DIR/${policy_type}.wasm" -i "$input_file" "data.fortress.runtime.performance_alert")
    
    if echo "$security_alerts" | jq -e '.result[0].expressions[0].value == true' > /dev/null; then
        error "SECURITY ALERT triggered!"
    fi
    
    if echo "$performance_alerts" | jq -e '.result[0].expressions[0].value == true' > /dev/null; then
        warn "Performance alert triggered"
    fi
}

# Generate test data
generate_test_data() {
    local data_dir="/tmp/fortress_test_data"
    mkdir -p "$data_dir"
    
    # Ledger test data
    cat > "$data_dir/ledger_valid.json" << 'EOF'
{
    "operation": "append",
    "subject": "test-transaction",
    "payload": "dGVzdCBwYXlsb2Fk",
    "meta": {
        "source": "api",
        "timestamp": "2023-12-01T10:00:00Z"
    },
    "require_signature": true
}
EOF

    cat > "$data_dir/ledger_invalid.json" << 'EOF'
{
    "operation": "append",
    "subject": "",
    "payload": "",
    "meta": {},
    "require_signature": true
}
EOF

    # API test data
    cat > "$data_dir/api_valid.json" << 'EOF'
{
    "method": "POST",
    "path": "/append",
    "headers": {
        "Authorization": "Bearer test-token-123",
        "Content-Type": "application/json"
    },
    "remote_addr": "192.168.1.100",
    "rate_limits": {
        "test-token-123": 30
    }
}
EOF

    cat > "$data_dir/api_invalid.json" << 'EOF'
{
    "method": "POST", 
    "path": "/append",
    "headers": {
        "Origin": "https://malicious.com"
    },
    "remote_addr": "192.168.1.100",
    "rate_limits": {
        "192.168.1.100": 100
    }
}
EOF

    # Runtime test data
    cat > "$data_dir/runtime_healthy.json" << 'EOF'
{
    "resource_type": "memory",
    "memory_mb": 256,
    "memory_growth_rate": 0.05,
    "cpu_percent": 45,
    "cpu_sustained_duration": 60,
    "connections_count": 500,
    "bandwidth_mbps": 50,
    "failed_auth_attempts": 2,
    "suspicious_patterns": 0,
    "payload_size": 1024
}
EOF

    cat > "$data_dir/runtime_unhealthy.json" << 'EOF'
{
    "resource_type": "memory",
    "memory_mb": 600,
    "memory_growth_rate": 0.15,
    "cpu_percent": 95,
    "cpu_sustained_duration": 400,
    "connections_count": 1200,
    "bandwidth_mbps": 150,
    "failed_auth_attempts": 25,
    "suspicious_patterns": 5,
    "payload_size": 15728640
}
EOF

    log "Test data generated in $data_dir"
    echo "$data_dir"
}

# Run comprehensive policy evaluation
run_evaluation_tests() {
    log "Running comprehensive policy evaluation tests..."
    
    local test_data_dir=$(generate_test_data)
    local all_passed=true
    
    # Test ledger policies
    log "Testing ledger policies..."
    if evaluate_ledger_policy "$test_data_dir/ledger_valid.json"; then
        success "Ledger valid case: PASSED"
    else
        error "Ledger valid case: FAILED" 
        all_passed=false
    fi
    
    if ! evaluate_ledger_policy "$test_data_dir/ledger_invalid.json"; then
        success "Ledger invalid case: PASSED (correctly denied)"
    else
        error "Ledger invalid case: FAILED (should have been denied)"
        all_passed=false
    fi
    
    # Test API policies
    log "Testing API policies..."
    if evaluate_api_policy "$test_data_dir/api_valid.json"; then
        success "API valid case: PASSED"
    else
        error "API valid case: FAILED"
        all_passed=false
    fi
    
    if ! evaluate_api_policy "$test_data_dir/api_invalid.json"; then
        success "API invalid case: PASSED (correctly denied)"
    else
        error "API invalid case: FAILED (should have been denied)"
        all_passed=false
    fi
    
    # Test runtime policies
    log "Testing runtime policies..."
    evaluate_runtime_policy "$test_data_dir/runtime_healthy.json"
    evaluate_runtime_policy "$test_data_dir/runtime_unhealthy.json"
    
    # Cleanup
    rm -rf "$test_data_dir"
    
    if [[ "$all_passed" == "true" ]]; then
        success "All policy evaluation tests passed"
        return 0
    else
        error "Some policy evaluation tests failed"
        return 1
    fi
}

# Monitor system in real-time
monitor_system() {
    local interval="${1:-5}"
    
    log "Starting real-time system monitoring (interval: ${interval}s)"
    log "Press Ctrl+C to stop"
    
    while true; do
        # Collect system metrics
        local memory_mb=$(free -m | awk '/^Mem:/ {print $3}')
        local cpu_percent=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        local connections=$(netstat -an | wc -l)
        
        # Create runtime input
        cat > /tmp/runtime_monitor.json << EOF
{
    "resource_type": "memory",
    "memory_mb": $memory_mb,
    "memory_growth_rate": 0.02,
    "cpu_percent": $cpu_percent,
    "cpu_sustained_duration": 60,
    "connections_count": $connections,
    "bandwidth_mbps": 10,
    "failed_auth_attempts": 0,
    "suspicious_patterns": 0,
    "payload_size": 1024
}
EOF
        
        # Evaluate runtime policy
        echo "--- $(date) ---"
        evaluate_runtime_policy /tmp/runtime_monitor.json
        
        sleep "$interval"
    done
}

# Main execution
main() {
    local command="${1:-evaluate}"
    
    case "$command" in
        "ledger")
            if [[ $# -lt 2 ]]; then
                error "Usage: $0 ledger <input_file>"
                exit 1
            fi
            evaluate_ledger_policy "$2"
            ;;
        "api")
            if [[ $# -lt 2 ]]; then
                error "Usage: $0 api <input_file>"
                exit 1
            fi
            evaluate_api_policy "$2"
            ;;
        "runtime")
            if [[ $# -lt 2 ]]; then
                error "Usage: $0 runtime <input_file>"
                exit 1
            fi
            evaluate_runtime_policy "$2"
            ;;
        "test")
            run_evaluation_tests
            ;;
        "monitor")
            local interval="${2:-5}"
            monitor_system "$interval"
            ;;
        *)
            echo "Fortress v4 Policy Evaluation Tool"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  ledger <input_file>   - Evaluate ledger policy"
            echo "  api <input_file>      - Evaluate API policy"
            echo "  runtime <input_file>  - Evaluate runtime policy"
            echo "  test                  - Run evaluation tests"
            echo "  monitor [interval]    - Real-time system monitoring"
            echo ""
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"