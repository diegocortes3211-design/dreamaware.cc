#!/bin/bash

# Build WASM bundle for Fortress authorization policy
# This script compiles the Rego policy into a WASM bundle using OPA

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
POLICY_DIR="$PROJECT_ROOT/policy/fortress"
OUTPUT_FILE="$POLICY_DIR/authz.wasm"

echo "Building Fortress authorization policy WASM bundle..."
echo "Policy directory: $POLICY_DIR"
echo "Output file: $OUTPUT_FILE"

# Check if OPA is installed
if ! command -v opa &> /dev/null; then
    echo "Error: OPA is not installed. Please install OPA first."
    echo "Visit: https://www.openpolicyagent.org/docs/latest/#running-opa"
    echo "Or install via: curl -L -o opa https://openpolicyagent.org/downloads/v0.57.0/opa_linux_amd64_static && chmod +x opa && sudo mv opa /usr/local/bin/"
    exit 1
fi

# Check if policy file exists
if [[ ! -f "$POLICY_DIR/authz.rego" ]]; then
    echo "Error: Policy file not found at $POLICY_DIR/authz.rego"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$POLICY_DIR"

# Build the WASM bundle
echo "Compiling policy to WASM..."
opa build -t wasm -e "data.fortress.authz.allow" "$POLICY_DIR/authz.rego"

# Move the generated bundle to the expected location
if [[ -f "bundle.tar.gz" ]]; then
    # Extract the WASM file from the bundle
    tar -xzf bundle.tar.gz
    if [[ -f "/policy.wasm" ]]; then
        mv /policy.wasm "$OUTPUT_FILE"
    elif [[ -f "policy.wasm" ]]; then
        mv policy.wasm "$OUTPUT_FILE"
    else
        echo "Error: Could not find policy.wasm in the generated bundle"
        exit 1
    fi
    
    # Clean up temporary files
    rm -f bundle.tar.gz
    
    echo "Successfully built WASM bundle: $OUTPUT_FILE"
    
    # Generate SHA-256 checksum for integrity verification
    if command -v sha256sum &> /dev/null; then
        CHECKSUM=$(sha256sum "$OUTPUT_FILE" | cut -d' ' -f1)
        echo "$CHECKSUM" > "$OUTPUT_FILE.sha256"
        echo "Generated checksum: $CHECKSUM"
        echo "Checksum saved to: $OUTPUT_FILE.sha256"
    else
        echo "Warning: sha256sum not available. Skipping checksum generation."
    fi
else
    echo "Error: Failed to generate bundle.tar.gz"
    exit 1
fi

echo "Policy build completed successfully!"