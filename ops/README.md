# Threat Scanning Operations Guide

This directory contains the infrastructure for authorized threat scanning using nmap with built-in safety controls and policy enforcement.

## 🛡️ Security Overview

This threat scanning system implements multiple layers of security controls:

- **Allowlist-based authorization**: Only pre-approved targets can be scanned
- **OPA policy enforcement**: All scans validated against defined policies  
- **Manual approval gates**: Production scans require explicit human approval
- **Bounded scan profiles**: Intensity levels prevent excessive network activity
- **Dry-run functionality**: Safe validation without actual network scanning
- **Audit logging**: All activities logged for compliance and security

## 📁 Directory Structure

```
ops/
├── README.md              # This file - operator documentation
├── targets-allow.txt      # Approved scanning targets (one per line)  
└── policy/
    ├── allowlist.json     # JSON allowlist for OPA policy evaluation
    └── scan.rego         # OPA policy rules for scan authorization
```

## 🎯 Approved Targets

Targets are defined in two places:

1. **`targets-allow.txt`** - Human-readable list of approved targets
2. **`policy/allowlist.json`** - JSON format with regex patterns for policy engine

### Adding New Targets

To add a new approved target:

1. Add the hostname/IP to `targets-allow.txt`
2. Add corresponding regex pattern to `policy/allowlist.json`
3. Submit PR for security team review
4. Requires security team approval before merge

Example target formats:
```
# Single hosts
example.com
192.168.1.100

# Network ranges (CIDR)
10.0.0.0/24
192.168.1.0/24
```

## 🔧 Scan Profiles

Three predefined scan profiles with bounded intensity:

### `recon` (Default - Safest)
- **Purpose**: Host discovery and basic reconnaissance
- **Nmap args**: `-sn -T2 --max-rate 100`
- **Impact**: Minimal network activity, ping-based discovery only
- **Use case**: Initial target validation, network mapping

### `light` (Moderate)
- **Purpose**: Basic port scanning of common services
- **Nmap args**: `-sS -T3 --top-ports 1000 --max-rate 300`  
- **Impact**: TCP SYN scan of top 1000 ports with moderate timing
- **Use case**: Service discovery, basic vulnerability assessment

### `full` (Comprehensive)
- **Purpose**: Detailed service enumeration and script scanning
- **Nmap args**: `-sS -sV -T4 --top-ports 5000 --max-rate 500 --script=default`
- **Impact**: Comprehensive scan with service detection and default scripts
- **Use case**: Thorough security assessment, penetration testing

## 🚀 Running Scans

### Via GitHub Actions (Recommended)

1. Navigate to **Actions** → **Authorized Threat Scanning**
2. Click **Run workflow**
3. Configure parameters:
   - **Target**: Hostname or IP (must be in allowlist)
   - **Profile**: Choose scan intensity (`recon`, `light`, `full`)
   - **Dry Run**: Enable for validation without actual scanning
   - **API Enrichment**: Enable Vulners API integration (optional)

### Production Scan Flow

1. **Policy Validation**: Target and profile validated against OPA policy
2. **Manual Approval**: Production scans require human approval in `threat-scanning-prod` environment
3. **Execution**: Scan runs with bounded parameters and timeout (30min max)
4. **Results**: Output artifacts available for 7 days (auto-deleted for security)

### Dry Run Testing

Always test with dry run first:
- Validates target against allowlist
- Confirms scan parameters
- No actual network activity
- Safe for testing configuration changes

## 🔒 Security Guardrails

### Built-in Protections

- **Action version pinning**: All actions use SHA-pinned versions
- **No pull request triggers**: Prevents untrusted code execution
- **Environment-based secrets**: API keys stored in GitHub environments, not repo
- **Log redaction**: Sensitive IPs replaced with `[REDACTED_IP]` in outputs
- **Artifact retention**: Scan results auto-deleted after 7 days
- **Rate limiting**: API calls bounded to prevent abuse
- **Timeout protection**: Maximum scan time of 30 minutes

### Environment Configuration

Create GitHub environment `threat-scanning-prod` with:
- **Required reviewers**: Security team members
- **Environment secrets**:
  - `VULNERS_API_KEY`: Optional API key for vulnerability enrichment

## 📋 OPA Policy Details

The `scan.rego` policy enforces:

- Target must match approved regex patterns
- Scan profile must be valid (`recon`, `light`, or `full`)
- Production scans require manual approval
- Dry runs always permitted for approved targets
- Input validation for IPs, hostnames, and CIDR notation

### Policy Testing

Test policy changes locally with OPA:

```bash
# Install OPA
curl -L -o opa https://openpolicyagent.org/downloads/v0.66.0/opa_linux_amd64_static
chmod 755 ./opa

# Test policy
./opa eval -d ops/policy/scan.rego -i input.json "data.scan.policy.allow"
```

Example `input.json`:
```json
{
  "target": "scanme.nmap.org",
  "profile": "recon", 
  "dry_run": true,
  "approval_required": false,
  "allowlist": { /* contents of allowlist.json */ }
}
```

## 🔍 API Enrichment

Optional integration with Vulners API for vulnerability intelligence:

- **Rate limited**: Maximum 10 API calls per scan
- **Service-based**: Enriches detected services with vulnerability data
- **Optional**: Disabled by default, requires API key configuration
- **Bounded**: Prevents API abuse with request limits

### Configuring API Enrichment

1. Obtain Vulners API key from https://vulners.com/
2. Add `VULNERS_API_KEY` to `threat-scanning-prod` environment secrets
3. Enable in workflow: Set "Enable Vulners API enrichment" to true

## 📊 Monitoring and Audit

### Audit Trail

All scan activities generate audit logs including:
- Requester identity (GitHub user)
- Target and scan parameters
- Approval status and approver
- Scan results summary
- Timestamp and duration

### Monitoring Endpoints

Monitor scan activity through:
- **GitHub Actions logs**: Detailed execution logs
- **Environment deployment logs**: Approval/rejection events  
- **Artifact downloads**: Access to scan results tracking

## 🚨 Incident Response

### Unauthorized Scan Attempts

If policy violations are detected:

1. **Immediate**: Scan is automatically blocked by OPA policy
2. **Investigation**: Review GitHub Actions logs for details
3. **Response**: Contact security team and requester
4. **Prevention**: Review and update allowlist/policy as needed

### False Positives

If legitimate targets are incorrectly blocked:

1. Verify target ownership and authorization
2. Update allowlist with proper approvals
3. Test with dry run before production use
4. Document justification in PR

## 🔧 Troubleshooting

### Common Issues

**"Target rejected by policy"**
- Check target exists in `targets-allow.txt` 
- Verify regex pattern in `allowlist.json`
- Use dry run to test policy validation

**"Manual approval required"**
- Production scans need security team approval
- Check `threat-scanning-prod` environment settings
- Ensure required reviewers are configured

**"API enrichment failed"**
- Verify `VULNERS_API_KEY` is set in environment
- Check API rate limits and quotas
- Review Vulners API documentation

**"Scan timeout"**
- Reduce scan intensity or target scope
- Check network connectivity to target
- Consider using `light` profile instead of `full`

## 📞 Support

For questions or issues:

1. **Security concerns**: Contact security team immediately
2. **Technical issues**: Create issue in repository  
3. **Policy changes**: Submit PR with security team review
4. **Emergency**: Follow incident response procedures

---

⚠️ **Important**: This tool performs active network reconnaissance. Ensure you have proper authorization before scanning any targets. Unauthorized scanning may violate terms of service, laws, or regulations.