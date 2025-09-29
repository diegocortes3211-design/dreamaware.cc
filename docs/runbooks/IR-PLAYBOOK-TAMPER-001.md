# IR-PLAYBOOK-TAMPER-001 — Merkle Integrity Violation

## 1) Detection & Triage
- **Trigger:** High-severity alert from MerkleIntegrityMonitor:
  - `integrity_root_mismatch` | `integrity_prefix_violation` | `integrity_timestamp_violation`
- **Actions (SEV-1):**
  - Incident Commander (IC) declares **Code Red: Data Integrity**.
  - Engage DB owner, Rank service owner, Security (DFIR), SRE on-call.

## 2) Containment
- Freeze writes:
  - Disable /rank/elo at gateway (feature flag) and revoke DB write creds for rank service.
- Isolate:
  - Quarantine rank service pods/VMs; snapshot disks; capture memory if feasible.
- Preserve:
  - Snapshot `match_events`, `merkle_roots`, and app logs; export outbox/security logs.

## 3) Eradication & Recovery
- Identify divergence point:
  - Using last known-good checkpoint from monitor (size S, root R), recompute roots from `match_events[1..S]` and binary-search forward to locate first mismatch.
- Restore:
  - Roll DB back to snapshot immediately prior to mismatch (immutable S3/ObjectLock).
  - Replay valid `match_events` after that point to current time; recompute Merkle roots and republish.
- Validate:
  - Run monitor in verification mode across full history; require **zero** anomalies.

## 4) Post-Incident
- Root Cause Analysis (RCA):
  - Was it data tamper, code path defect, clock abuse, or key compromise?
- Remediation:
  - Tighten privileges; add policy/controls; extend alerts.
- Evidence package:
  - Bundle monitor alerts, recomputation transcripts, restored roots, and operator actions for audit.

**SLAs**
- Detection: ≤ 5 min
- Containment start: ≤ 15 min
- Verified restoration: ≤ 4 hours

**Contacts**
- IC: …
- DB Owner: …
- Rank Svc: …
- Security: …