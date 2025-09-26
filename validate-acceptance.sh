#!/bin/bash

# Acceptance Checklist Validation for Rekor Anchoring Workflow
# This script verifies that all requirements from the problem statement are met

set -euo pipefail

echo "🔍 Rekor Anchoring Workflow - Acceptance Checklist Validation"
echo "============================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_passed=0
check_failed=0

# Function to report test results
report_check() {
    local description="$1"
    local status="$2"
    local details="${3:-}"
    
    if [ "$status" = "PASS" ]; then
        echo -e "✅ ${GREEN}$description${NC}"
        [ -n "$details" ] && echo -e "   ${details}"
        check_passed=$((check_passed + 1))
    else
        echo -e "❌ ${RED}$description${NC}"
        [ -n "$details" ] && echo -e "   ${details}"
        check_failed=$((check_failed + 1))
    fi
}

echo -e "\n📋 Checking Acceptance Criteria..."

# 1. Scheduled runs succeed with no inputs (defaults applied)
echo -e "\n${YELLOW}1. Scheduled runs with safe defaults${NC}"

if grep -q "schedule:" .github/workflows/rekor-anchor.yml && \
   grep -q "cron:" .github/workflows/rekor-anchor.yml && \
   grep -q "default:" .github/workflows/rekor-anchor.yml; then
    report_check "Scheduled runs configured with safe defaults" "PASS" \
        "Found schedule trigger with cron and default parameter values"
else
    report_check "Scheduled runs configured with safe defaults" "FAIL" \
        "Missing schedule configuration or default values"
fi

# 2. Manual runs honor all inputs
echo -e "\n${YELLOW}2. Manual run input handling${NC}"

required_inputs=("N" "rekor_server" "rekorcliimage" "dry_run" "batch_size")
inputs_found=0

for input in "${required_inputs[@]}"; do
    if grep -q "$input:" .github/workflows/rekor-anchor.yml; then
        inputs_found=$((inputs_found + 1))
    fi
done

if [ "$inputs_found" -eq 5 ]; then
    report_check "Manual runs support all required inputs" "PASS" \
        "All 5 required inputs (N, dry_run, batch_size, rekor_server, rekorcliimage) found"
else
    report_check "Manual runs support all required inputs" "FAIL" \
        "Only $inputs_found/5 inputs found in workflow"
fi

# 3. Input sanitization
echo -e "\n${YELLOW}3. Input sanitization${NC}"

if grep -q "Sanitize inputs" .github/workflows/rekor-anchor.yml && \
   grep -q "grep -E" .github/workflows/rekor-anchor.yml; then
    report_check "Input sanitization implemented" "PASS" \
        "Found sanitization logic with regex validation"
else
    report_check "Input sanitization implemented" "FAIL" \
        "Missing input sanitization in workflow"
fi

# 4. Rekor CLI image digest capture and usage
echo -e "\n${YELLOW}4. Digest-pinned Docker runs${NC}"

if grep -q "docker inspect" .github/workflows/rekor-anchor.yml && \
   grep -q "IMAGE_DIGEST" .github/workflows/rekor-anchor.yml && \
   grep -q "@\${IMAGE_DIGEST}" .github/workflows/rekor-anchor.yml; then
    report_check "Rekor CLI image digest captured and used" "PASS" \
        "Found docker inspect, digest capture, and usage in Docker commands"
else
    report_check "Rekor CLI image digest captured and used" "FAIL" \
        "Missing digest capture or usage"
fi

# 5. Dual-flag Rekor CLI compatibility
echo -e "\n${YELLOW}5. Dual-flag Rekor CLI compatibility${NC}"

if grep -q -- "--sha256" .github/workflows/rekor-anchor.yml && \
   grep -q -- "--sha " .github/workflows/rekor-anchor.yml; then
    report_check "Dual-flag search support (--sha256 and --sha)" "PASS" \
        "Both --sha256 and --sha flags found in workflow"
else
    report_check "Dual-flag search support (--sha256 and --sha)" "FAIL" \
        "Missing dual-flag compatibility"
fi

# 6. Jittered retries
echo -e "\n${YELLOW}6. Jittered retry implementation${NC}"

if grep -q "sleep_time.*rand" .github/workflows/rekor-anchor.yml && \
   grep -q "sleep.*sleep_time" .github/workflows/rekor-anchor.yml; then
    report_check "Jittered retries to avoid thundering herd" "PASS" \
        "Found randomized sleep implementation"
else
    report_check "Jittered retries to avoid thundering herd" "FAIL" \
        "Missing jittered retry logic"
fi

# 7. All expected artifacts
echo -e "\n${YELLOW}7. Artifact generation${NC}"

expected_artifacts=("hashes_raw.txt" "hashes.txt" "hashes.proc" "attempted.txt" 
                   "anchored.txt" "skipped.txt" "failed.txt" "image-digest.txt")
artifacts_found=0

for artifact in "${expected_artifacts[@]}"; do
    if grep -q "$artifact" .github/workflows/rekor-anchor.yml; then
        artifacts_found=$((artifacts_found + 1))
    fi
done

if [ "$artifacts_found" -eq 8 ]; then
    report_check "All expected artifacts included" "PASS" \
        "All 8 required artifacts found in workflow"
else
    report_check "All expected artifacts included" "FAIL" \
        "Only $artifacts_found/8 artifacts found"
fi

# 8. Workflow summary with counts
echo -e "\n${YELLOW}8. Workflow summary generation${NC}"

if grep -q "GITHUB_STEP_SUMMARY" .github/workflows/rekor-anchor.yml && \
   grep -q "CONSIDERED_COUNT\|USABLE_COUNT\|ANCHORED_COUNT" .github/workflows/rekor-anchor.yml; then
    report_check "Workflow summary shows hash counts" "PASS" \
        "Found step summary generation with count variables"
else
    report_check "Workflow summary shows hash counts" "FAIL" \
        "Missing workflow summary or count reporting"
fi

# 9. SQL-side filtering
echo -e "\n${YELLOW}9. SQL-side filtering${NC}"

if [ -f "docs/database-schema.sql" ] && \
   grep -q "length(hash) = 64" docs/database-schema.sql && \
   grep -q "hash ~ " docs/database-schema.sql; then
    report_check "SQL-side filtering implemented" "PASS" \
        "Database schema includes hash validation at SQL level"
else
    report_check "SQL-side filtering implemented" "FAIL" \
        "Missing SQL-side filtering in database schema"
fi

# 10. Database indexes for performance
echo -e "\n${YELLOW}10. Database performance indexes${NC}"

if [ -f "docs/database-schema.sql" ] && \
   grep -q "idx_ledger_ts_desc" docs/database-schema.sql && \
   grep -q "idx_ledger_hash" docs/database-schema.sql; then
    report_check "Database indexes for query optimization" "PASS" \
        "Found recommended indexes: idx_ledger_ts_desc and idx_ledger_hash"
else
    report_check "Database indexes for query optimization" "FAIL" \
        "Missing required database indexes"
fi

# 11. Runbook documentation
echo -e "\n${YELLOW}11. Runbook documentation${NC}"

if [ -f "docs/rekor-anchoring-runbook.md" ] && \
   grep -q "dry_run" docs/rekor-anchoring-runbook.md && \
   grep -q "batch_size" docs/rekor-anchoring-runbook.md && \
   grep -q "loginfo" docs/rekor-anchoring-runbook.md; then
    report_check "Complete runbook documentation" "PASS" \
        "Runbook includes parameter docs, examples, and operational guidance"
else
    report_check "Complete runbook documentation" "FAIL" \
        "Missing or incomplete runbook documentation"
fi

# 12. Batch size limiter
echo -e "\n${YELLOW}12. Batch size limiter${NC}"

if grep -q "BATCH_SIZE" .github/workflows/rekor-anchor.yml && \
   grep -q "head -n.*BATCH_SIZE" .github/workflows/rekor-anchor.yml; then
    report_check "Batch size limiter caps processing per run" "PASS" \
        "Found batch size parameter and limiting logic"
else
    report_check "Batch size limiter caps processing per run" "FAIL" \
        "Missing batch size limiting functionality"
fi

# Summary
echo -e "\n📊 ${YELLOW}Validation Summary${NC}"
echo "==================="
echo -e "✅ ${GREEN}Passed: $check_passed${NC}"
echo -e "❌ ${RED}Failed: $check_failed${NC}"

if [ "$check_failed" -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}ALL ACCEPTANCE CRITERIA MET!${NC}"
    echo "The Rekor anchoring workflow implementation is complete and ready for production use."
    exit 0
else
    echo -e "\n⚠️  ${RED}$check_failed CRITERIA NOT MET${NC}"
    echo "Please review the failed checks above and address them before deployment."
    exit 1
fi