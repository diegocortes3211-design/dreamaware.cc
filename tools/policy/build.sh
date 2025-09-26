#!/bin/bash
# Fortress v4 Policy Build and Test Script
# Builds OPA policies into WASM bundles and runs tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
POLICY_DIR="${PROJECT_ROOT}/policy"
OUTPUT_DIR="${PROJECT_ROOT}/dist/policy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if OPA is installed
check_opa() {
    if ! command -v opa &> /dev/null; then
        error "OPA is not installed. Please install OPA first:"
        error "  curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static"
        error "  chmod 755 ./opa"
        error "  sudo mv ./opa /usr/local/bin/"
        exit 1
    fi
    log "OPA version: $(opa version | head -1)"
}

# Run policy tests
run_tests() {
    log "Running OPA policy tests..."
    
    local test_failed=false
    
    # Test each policy file
    for test_file in "${POLICY_DIR}/tests"/*.rego; do
        if [[ -f "$test_file" ]]; then
            log "Testing $(basename "$test_file")"
            if ! opa test "${POLICY_DIR}/rego" "$test_file"; then
                error "Tests failed for $(basename "$test_file")"
                test_failed=true
            fi
        fi
    done
    
    if [[ "$test_failed" == "true" ]]; then
        error "Some policy tests failed"
        exit 1
    fi
    
    success "All policy tests passed"
}

# Build WASM bundles
build_wasm() {
    log "Building WASM bundles..."
    
    mkdir -p "$OUTPUT_DIR"
    
    # Build each policy package into WASM
    local packages=("fortress.ledger" "fortress.api" "fortress.runtime")
    
    for package in "${packages[@]}"; do
        local output_file="${OUTPUT_DIR}/${package##*.}.wasm"
        log "Building WASM bundle for package $package"
        
        if opa build -t wasm -e "$package/allow" "${POLICY_DIR}/rego" -o "$output_file"; then
            success "Built $output_file"
            log "Bundle size: $(du -h "$output_file" | cut -f1)"
        else
            error "Failed to build WASM bundle for $package"
            exit 1
        fi
    done
}

# Validate policy syntax
validate_policies() {
    log "Validating policy syntax..."
    
    for rego_file in "${POLICY_DIR}/rego"/*.rego; do
        if [[ -f "$rego_file" ]]; then
            log "Validating $(basename "$rego_file")"
            if ! opa fmt --diff "$rego_file" > /dev/null; then
                warn "Policy file $(basename "$rego_file") is not formatted correctly"
                log "Run: opa fmt --write $rego_file"
            fi
        fi
    done
    
    # Check for compilation errors
    if opa build "${POLICY_DIR}/rego" > /dev/null 2>&1; then
        success "All policies compile successfully"
    else
        error "Policy compilation failed"
        opa build "${POLICY_DIR}/rego"
        exit 1
    fi
}

# Format policy files
format_policies() {
    log "Formatting policy files..."
    
    find "${POLICY_DIR}" -name "*.rego" -exec opa fmt --write {} \;
    success "Policy files formatted"
}

# Generate policy documentation
generate_docs() {
    log "Generating policy documentation..."
    
    local docs_dir="${OUTPUT_DIR}/docs"
    mkdir -p "$docs_dir"
    
    # Extract comments and rules for documentation
    cat > "${docs_dir}/policy_reference.md" << 'EOF'
# Fortress v4 Policy Reference

This document provides an overview of the policies implemented in Fortress v4.

## Policy Packages

### fortress.ledger
Validates ledger append requests with the following rules:
- Subject validation (non-empty, alphanumeric, max 256 chars)
- Payload validation (non-empty, max 1MB)
- Metadata validation (valid object structure)
- Signature requirement enforcement
- Rate limiting checks

### fortress.api  
Controls API access with the following rules:
- Authentication header validation
- Rate limiting per client
- CORS validation
- Security header checks
- Request size limits

### fortress.runtime
Monitors system resources and security with the following rules:
- Memory usage limits (512MB max, 10% growth rate)
- CPU usage limits (80% max, 5 minute sustained duration)
- Network connection limits (1000 connections max, 100Mbps)
- Database connection pool monitoring
- WebSocket connection limits
- Security alert triggers
- Performance monitoring

## Usage

Policies are compiled into WASM bundles and can be evaluated using the OPA runtime or integrated into applications.

EOF

    success "Policy documentation generated at ${docs_dir}/policy_reference.md"
}

# Performance benchmarking
benchmark_policies() {
    log "Running policy performance benchmarks..."
    
    # Create test data for benchmarking
    cat > /tmp/bench_data.json << 'EOF'
{
    "operation": "append",
    "subject": "benchmark-test",
    "payload": "dGVzdCBwYXlsb2FkIGZvciBiZW5jaG1hcmtpbmc=",
    "meta": {"source": "benchmark", "timestamp": "2023-12-01T10:00:00Z"},
    "require_signature": true
}
EOF
    
    log "Benchmarking ledger validation policy..."
    opa bench "${POLICY_DIR}/rego/ledger_validation.rego" --data /tmp/bench_data.json --count 1000
    
    # Cleanup
    rm -f /tmp/bench_data.json
}

# Main execution
main() {
    local command="${1:-all}"
    
    log "Starting Fortress v4 Policy Build Process"
    log "Policy directory: $POLICY_DIR"
    log "Output directory: $OUTPUT_DIR"
    
    check_opa
    
    case "$command" in
        "test")
            run_tests
            ;;
        "build")
            validate_policies
            build_wasm
            ;;
        "format")
            format_policies
            ;;
        "docs")
            generate_docs
            ;;
        "benchmark")
            benchmark_policies
            ;;
        "all")
            validate_policies
            format_policies
            run_tests
            build_wasm
            generate_docs
            ;;
        *)
            error "Unknown command: $command"
            echo "Usage: $0 [test|build|format|docs|benchmark|all]"
            exit 1
            ;;
    esac
    
    success "Policy build process completed successfully"
}

# Run main function with all arguments
main "$@"