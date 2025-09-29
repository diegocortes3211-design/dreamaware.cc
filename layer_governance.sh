#!/usr/bin/env bash
# Psychoid Nexus — Governance Gates (DRY-RUN+ARTIFACTS)
set -euo pipefail

# 0) Sanity
if [ ! -d .git ]; then
  echo "[-] Please run from the psychoid-nexus repo root (must be a git repo)."
  exit 1
fi

echo "[+] Creating governance directories..."
mkdir -p configs/schemas \
         configs/policies/opa \
         ci/pipelines \
         .github/workflows \
         configs/risk_records \
         configs/oversight/approvals

# 1) JSON Schemas (risk + oversight)
echo "[+] Writing configs/schemas/risk_assessment.json"
cat > configs/schemas/risk_assessment.json <<'JSON'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RiskAssessment",
  "type": "object",
  "required": ["use_case","impact","controls","owner","signoff_hash"],
  "properties": {
    "use_case": { "type": "string" },
    "impact":   { "type": "string", "enum": ["low","medium","high","critical"] },
    "controls": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["bias","explainability","rollback","redteam","privacy","safety_override"]
      },
      "minItems": 1
    },
    "owner":        { "type": "string" },
    "signoff_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "notes":        { "type": "string" }
  },
  "additionalProperties": false
}
JSON

echo "[+] Writing configs/schemas/oversight_approval.json"
cat > configs/schemas/oversight_approval.json <<'JSON'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OversightApproval",
  "type": "object",
  "required": ["approver","approver_role","decision","root_hash","timestamp"],
  "properties": {
    "approver":      { "type": "string" },
    "approver_role": { "type": "string", "enum": ["CAIO","CISO"] },
    "decision":      { "type": "string", "enum": ["approve","reject","conditional_approve"] },
    "root_hash":     { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "timestamp":     { "type": "string", "format": "date-time" },
    "conditions":    { "type": "array", "items": { "type": "string" } },
    "notes":         { "type": "string" }
  },
  "additionalProperties": false
}
JSON

# 2) OPA policy (capabilities allowlist) + unit tests
echo "[+] Writing OPA policy: configs/policies/opa/agent_permissions.rego"
cat > configs/policies/opa/agent_permissions.rego <<'REGO'
package agent.permissions

# Default: deny
default allow = false

# Allowed capabilities (tighten/expand over time)
allowed_capabilities[c] { c := "biology.query" }
allowed_capabilities[c] { c := "biology.spawn_entity" }
allowed_capabilities[c] { c := "network.access" }
allowed_capabilities[c] { c := "storage.read" }
allowed_capabilities[c] { c := "storage.write" }

# Allow only if every requested capability is in the allowed set
allow {
  input.capabilities
  not exists_disallowed
}

exists_disallowed {
  c := input.capabilities[_]
  not allowed_capabilities[c]
}
REGO

echo "[+] Writing OPA unit tests: configs/policies/opa/agent_permissions_test.rego"
cat > configs/policies/opa/agent_permissions_test.rego <<'REGO'
package agent.permissions

test_allow_all_good {
  data.agent.permissions.allow with input as {"capabilities": ["network.access","storage.read"]}
}

test_deny_unlisted_capability {
  not data.agent.permissions.allow with input as {"capabilities": ["fs.root"]}
}

test_deny_empty_list {
  not data.agent.permissions.allow with input as {"capabilities": []}
}
REGO

# 3) Reusable Governance Gate workflow (GitHub Actions)
# NOTE: Reusable workflows must live under .github/workflows and be referenced as owner/repo/.github/workflows/<file>@ref
echo "[+] Writing reusable workflow: .github/workflows/governance-gate.yml"
cat > .github/workflows/governance-gate.yml <<'YAML'
name: Governance Gate (reusable)

on:
  workflow_call:
    inputs:
      pr_number:
        description: "Pull Request number to validate"
        required: true
        type: number

jobs:
  governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Compute changed files
        id: diff
        run: |
          git fetch origin "${{ github.base_ref }}" --depth=1 || true
          git diff --name-only "origin/${{ github.base_ref }}"... > changed.txt || true
          cat changed.txt

      - name: Determine if risk record required
        id: needs_risk
        run: |
          if grep -E '^(engine|simulation|workshop|adversarial|services|physics-engine)/' changed.txt; then
            echo "required=true" >> "$GITHUB_OUTPUT"
          else
            echo "required=false" >> "$GITHUB_OUTPUT"
          fi

      - name: Install validators (check-jsonschema + OPA)
        run: |
          python3 -m pip install --upgrade pip >/dev/null
          python3 -m pip install check-jsonschema >/dev/null
          curl -sSL -o opa https://openpolicyagent.org/downloads/v0.63.0/opa_linux_amd64_static
          chmod +x opa
          ./opa version

      - name: Validate risk record (when required)
        if: steps.needs_risk.outputs.required == 'true'
        run: |
          PR=${{ inputs.pr_number }}
          FILE="configs/risk_records/${PR}.yaml"
          test -f "$FILE" || (echo "::error::Missing $FILE" && exit 1)
          check-jsonschema --schemafile configs/schemas/risk_assessment.json "$FILE"

      - name: Validate oversight approval (when PR labeled high-impact)
        if: contains(github.event.pull_request.labels.*.name, 'high-impact')
        run: |
          PR=${{ inputs.pr_number }}
          FILE="configs/oversight/approvals/${PR}.yaml"
          test -f "$FILE" || (echo "::error::Missing $FILE (required for 'high-impact' PRs)" && exit 1)
          check-jsonschema --schemafile configs/schemas/oversight_approval.json "$FILE"

      - name: Run OPA policy tests
        run: ./opa test configs/policies/opa -v
YAML

# 4) PR Gate that calls the reusable workflow
echo "[+] Wiring PR gate: .github/workflows/pr-gate.yml"
REPO_PATH="${GITHUB_REPOSITORY:-$(
  git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+/.+)\.git#\1#'
)}"
# Fallback if no remote yet:
if [ -z "$REPO_PATH" ]; then REPO_PATH="dreamaware-ai/psychoid-nexus"; fi

cat > .github/workflows/pr-gate.yml <<YAML
name: PR Governance Gate
on:
  pull_request:
    types: [opened, reopened, synchronize, edited, labeled]

jobs:
  governance-gate:
    uses: ${REPO_PATH}/.github/workflows/governance-gate.yml@main
    with:
      pr_number: \${{ github.event.pull_request.number }}
YAML

# (Optional) keep a copy under ci/pipelines for docs/discovery
echo "[+] Mirroring reusable workflow under ci/pipelines/governance-gate.yml (doc copy)"
cp .github/workflows/governance-gate.yml ci/pipelines/governance-gate.yml || true

# 5) Append governance sections to module READMEs
echo "[+] Appending governance sections to module READMEs..."
append_section() {
  local f="$1"
  # Create the file if it doesn't exist
  if [ ! -f "$f" ]; then
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$f")"
    touch "$f"
  fi
  if grep -q "## Governance" "$f"; then
    echo "  - $f already has Governance section."
  else
    cat >> "$f" <<'MD'

## Governance

**Risk Assessment**
- Provide `configs/risk_records/<PR_NUMBER>.yaml` (schema: `configs/schemas/risk_assessment.json`).

**Oversight (when labeled `high-impact`)**
- Provide `configs/oversight/approvals/<PR_NUMBER>.yaml` (schema: `configs/schemas/oversight_approval.json`).

**Policies & CI**
- OPA policy: `configs/policies/opa/agent_permissions.rego` (tests in same folder).
- Blocking CI: `.github/workflows/pr-gate.yml` → triggers the reusable Governance Gate.
MD
    echo "  - Appended governance section to $f"
  fi
}
for d in engine simulation physics-engine workshop adversarial spherefold neuroanalysis; do
  append_section "$d/README.md"
done

echo "[✓] Governance layer applied."
echo
echo "Next steps:"
echo "  1) Mark PRs as 'high-impact' when needed (requires oversight YAML)."
echo "  2) Add a risk record for PR #123: configs/risk_records/123.yaml"
echo "  3) (Optional) Tune OPA allowed capabilities."
echo
echo "Quick test (local):"
echo "  - Create a sample risk record under configs/risk_records/1.yaml and push a PR touching 'engine/'."
echo "  - The PR should be blocked unless the YAML validates against the schema."