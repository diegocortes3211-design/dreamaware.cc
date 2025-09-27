---
id: security
title: Security Policy
---

# Security Policy

This project follows Zero Trust and DevSecOps practices.

High level:
1. Least privilege for identities and services.
2. Strong auth for all traffic. Prefer mTLS for service calls.
3. Secrets from a manager. No long lived keys in env.
4. Audit every LLM call with prompt hashing and metadata.
5. Defend against prompt injection with guard checks.
6. Supply chain integrity with SBOM and scanners.

Operational controls:
- Pre commit hook strips slop and removes risky unicode.
- SAST and secret scans run for every PR.
- SBOM generated on every main push.
- Router has circuit breaker and fallbacks to keep SLOs.

Configuration:
- Optional mTLS: set CA_BUNDLE_PATH, CLIENT_CERT_PATH, CLIENT_KEY_PATH.
- Circuit breaker: CB_MAX_FAILS, CB_RESET_SEC.
- HTTP timeouts: HTTP_TIMEOUT_SEC.