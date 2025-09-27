---
id: SSRF
title: SSRF Guard and URL Allowlist
---

This service enforces a strict server side request forgery guard for all outbound HTTP requests.

Protections:
1. Scheme: only http and https.
2. Credentials: userinfo in URLs is rejected.
3. Ports: only 80 and 443.
4. Allowlist: hostname must match or be a subdomain of an entry in `configs/url_allowlist.yaml`.
5. DNS: resolve all A and AAAA results and block loopback, private, link local, multicast, CGNAT, and reserved ranges.
6. Redirects: every redirect target is revalidated.

To add a new source, submit a PR that updates:
```yaml
allowed_domains:
  - github.com
  - raw.githubusercontent.com
  - dreamaware.cc
  - new-trusted-source.com
```

Operational notes:
- Changes to the allowlist are loaded at runtime.
- Unit tests cover private IP blocking, scheme enforcement, suffix matching, and disallowing non default ports.