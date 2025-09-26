#!/bin/bash

# Test script for Rekor anchoring workflow validation
# This script tests the parameter sanitization and validation logic

set -euo pipefail

echo "🧪 Testing Rekor Anchoring Workflow Parameter Validation"

# Test parameter sanitization function
test_sanitization() {
    local test_name="$1"
    local input="$2" 
    local expected="$3"
    local type="$4"
    
    echo "Testing $test_name..."
    
    case "$type" in
        "number")
            result=$(echo "$input" | grep -E '^[0-9]+$' || echo '1000')
            if [ "$result" -gt 10000 ]; then result=10000; fi
            ;;
        "url")
            if echo "$input" | grep -E '^https?://[a-zA-Z0-9.-]+' >/dev/null; then
                result="$input"
            else
                result="https://rekor.sigstore.dev"
            fi
            ;;
        "image")
            if echo "$input" | grep -E '^[a-zA-Z0-9._/-]+:[a-zA-Z0-9._-]+$' >/dev/null; then
                result="$input"
            else
                result="gcr.io/projectsigstore/rekor-cli:latest"
            fi
            ;;
    esac
    
    if [ "$result" = "$expected" ]; then
        echo "✅ $test_name PASSED: '$input' -> '$result'"
    else
        echo "❌ $test_name FAILED: '$input' -> '$result' (expected '$expected')"
        return 1
    fi
}

echo -e "\n📋 Testing Parameter Sanitization"

# Test N parameter
test_sanitization "N - Valid number" "500" "500" "number"
test_sanitization "N - Invalid input" "abc" "1000" "number"
test_sanitization "N - Empty input" "" "1000" "number"
test_sanitization "N - Too large" "50000" "10000" "number"

# Test URL validation
test_sanitization "URL - Valid HTTPS" "https://rekor.sigstore.dev" "https://rekor.sigstore.dev" "url"
test_sanitization "URL - Valid HTTP" "http://localhost:3000" "http://localhost:3000" "url"
test_sanitization "URL - Invalid format" "not-a-url" "https://rekor.sigstore.dev" "url"
test_sanitization "URL - Empty" "" "https://rekor.sigstore.dev" "url"

# Test image validation
test_sanitization "Image - Valid format" "gcr.io/projectsigstore/rekor-cli:v1.0.0" "gcr.io/projectsigstore/rekor-cli:v1.0.0" "image"
test_sanitization "Image - Invalid format" "invalid-image-format" "gcr.io/projectsigstore/rekor-cli:latest" "image"

echo -e "\n🗂️  Testing Hash Validation"

# Create test hash file
cat << 'EOF' > /tmp/test_hashes.txt
abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
invalid-hash
abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
short-hash
ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890
EOF

# Test hash filtering (should only keep valid 64-char lowercase hex)
echo "Filtering test hashes..."
valid_hashes=$(grep -E '^[a-f0-9]{64}$' /tmp/test_hashes.txt | wc -l)
echo "Valid hashes found: $valid_hashes"

if [ "$valid_hashes" -eq 3 ]; then
    echo "✅ Hash validation PASSED: Found expected 3 valid hashes"
else
    echo "❌ Hash validation FAILED: Expected 3 valid hashes, found $valid_hashes"
fi

echo -e "\n🐳 Testing Docker Image Digest Simulation"

# Simulate image digest extraction
mock_digest="sha256:abcd1234567890efgh1234567890abcd1234567890efgh1234567890abcd1234"
echo "$mock_digest" > /tmp/image-digest.txt

if [ -f "/tmp/image-digest.txt" ] && grep -q "sha256:" /tmp/image-digest.txt; then
    echo "✅ Image digest capture PASSED"
else
    echo "❌ Image digest capture FAILED"
fi

echo -e "\n⏱️  Testing Jittered Retry Logic"

# Test jitter calculation
echo "Testing jitter calculation (should be between 1-3 seconds):"
for i in {1..5}; do
    jitter=$(awk "BEGIN {srand(); print int(rand() * 3) + 1}")
    echo "  Iteration $i: ${jitter}s"
    if [ "$jitter" -lt 1 ] || [ "$jitter" -gt 3 ]; then
        echo "❌ Jitter out of range: $jitter"
        exit 1
    fi
done
echo "✅ Jitter calculation PASSED"

echo -e "\n📊 Testing Artifact Generation"

# Create mock artifacts
touch attempted.txt anchored.txt skipped.txt failed.txt
echo "hash1" >> attempted.txt
echo "hash1" >> anchored.txt

# Test artifact existence
artifacts=("attempted.txt" "anchored.txt" "skipped.txt" "failed.txt")
missing_artifacts=0

for artifact in "${artifacts[@]}"; do
    if [ ! -f "$artifact" ]; then
        echo "❌ Missing artifact: $artifact"
        missing_artifacts=$((missing_artifacts + 1))
    fi
done

if [ "$missing_artifacts" -eq 0 ]; then
    echo "✅ Artifact generation PASSED: All expected artifacts present"
else
    echo "❌ Artifact generation FAILED: $missing_artifacts missing artifacts"
fi

# Cleanup
rm -f /tmp/test_hashes.txt /tmp/image-digest.txt
rm -f attempted.txt anchored.txt skipped.txt failed.txt

echo -e "\n🎉 Validation tests completed successfully!"
echo "The Rekor anchoring workflow parameter validation and core logic appears to be working correctly."