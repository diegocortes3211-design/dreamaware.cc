
## Governance

**Risk Assessment**
- Provide `configs/risk_records/<PR_NUMBER>.yaml` (schema: `configs/schemas/risk_assessment.json`).

**Oversight (when labeled `high-impact`)**
- Provide `configs/oversight/approvals/<PR_NUMBER>.yaml` (schema: `configs/schemas/oversight_approval.json`).

**Policies & CI**
- OPA policy: `configs/policies/opa/agent_permissions.rego` (tests in same folder).
- Blocking CI: `.github/workflows/pr-gate.yml` → triggers the reusable Governance Gate.
