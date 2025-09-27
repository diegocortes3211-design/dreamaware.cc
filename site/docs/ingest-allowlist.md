---
id: ingest-allowlist
title: Ingestion URL Allowlist and SSRF Guard
---

This platform enforces a secure default for external ingestion. All http and https sources pass through a URL verifier that:

1.  Restricts schemes to http or https.
2.  Enforces a host allowlist.
3.  Resolves DNS and rejects private, loopback, link local, and multicast IPs.
4.  Normalizes the URL and blocks oversized responses.

### Manage the allowlist
Edit `configs/url_allowlist.yaml` and submit a PR. Example:

```yaml
allowed_domains:
  - github.com
  - raw.githubusercontent.com
  - diegocortes3211-design.github.io
  - dreamaware.cc
```
Changes are reviewed in code review and take effect on merge. No service restart is required if your deployment mounts configs dynamically.

### CLI usage
The ingestion worker treats the --source argument as a URL by default. If it does not start with http or https, it is read as a local file with a size cap.
`apps/worker/ingest_worker.py --source https://github.com/diegocortes3211-design/dreamaware.cc/README.md --query "summarize"`

### Security notes
* Do not add wildcards that grant entire TLDs.
* Prefer adding only the exact hosts you control.
* For temporary testing, use a feature branch allowlist and remove it before release.