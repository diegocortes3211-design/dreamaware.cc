#!/bin/bash
# Test script to validate Rekor anchoring workflow components locally
# This script simulates the workflow steps without actually anchoring to Rekor

set -e

echo "🔍 Testing Rekor Anchoring Workflow Components"
echo "=============================================="

# Test 1: Hash generation
echo "Test 1: Hash Generation"
echo "----------------------"
mkdir -p test_output/hashes
find . -type f -not -path './.git/*' -not -path './node_modules/*' -not -path './test_output/*' \
  -exec sha256sum {} \; > test_output/hashes/hashes_raw.txt

hash_count=$(wc -l < test_output/hashes/hashes_raw.txt)
echo "✅ Generated $hash_count file hashes"

# Test 2: Clean hash extraction  
cut -d' ' -f1 test_output/hashes/hashes_raw.txt > test_output/hashes/hashes.txt
clean_count=$(wc -l < test_output/hashes/hashes.txt)
echo "✅ Extracted $clean_count clean hashes"

# Test 3: Directory structure
echo -e "\nTest 2: Directory Structure"
echo "---------------------------"
mkdir -p test_output/entries
echo "✅ Created entries directory"

# Test 4: Simulate dry run processing
echo -e "\nTest 3: Dry Run Simulation"
echo "--------------------------"
success_count=0
failure_count=0

while IFS= read -r hash; do
  if [[ -z "$hash" ]]; then
    continue
  fi
  echo "[DRY RUN] Would anchor hash: ${hash:0:16}..."
  success_count=$((success_count + 1))
  # Simulate creating a mock inclusion proof
  mock_uuid="${hash:0:64}"
  echo "{\"uuid\":\"$mock_uuid\",\"mock\":true}" > "test_output/entries/${mock_uuid}.json"
done < test_output/hashes/hashes.txt

echo "✅ Dry run complete: $success_count hashes processed"

# Test 5: Summary creation
echo -e "\nTest 4: Artifact Summary"
echo "------------------------"
cat > test_output/artifact_summary.txt << EOF
Rekor Anchoring Test Summary
============================

Run Date: $(date -u)
Hash Count: $hash_count
Successful: $success_count
Failed: $failure_count
Dry Run: true
Capture Proofs: true
Verify Image: false
Fail on Failed: false
EOF

echo "✅ Created artifact summary"

# Test 6: Validate outputs
echo -e "\nTest 5: Output Validation"
echo "-------------------------"
echo "Hash files:"
ls -la test_output/hashes/
echo -e "\nInclusion proof files:"
ls -la test_output/entries/ | head -10
if [[ $(find test_output/entries -name "*.json" | wc -l) -gt 0 ]]; then
  echo "✅ $(find test_output/entries -name "*.json" | wc -l) inclusion proof files created"
fi

echo -e "\nArtifact summary:"
cat test_output/artifact_summary.txt

echo -e "\n🎉 All tests passed successfully!"
echo "Files created in test_output/ directory:"
find test_output -type f | sort

echo -e "\nCleaning up test files..."
rm -rf test_output/
echo "✅ Cleanup complete"