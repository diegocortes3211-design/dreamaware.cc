# Security Policy for DreamAware Ledger Service

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

### Security Issues

If you discover a security vulnerability in the DreamAware Ledger Service, please follow these steps:

1. **Do NOT open a public issue** - Security vulnerabilities should be reported privately
2. Create a private security advisory on GitHub or email security@dreamaware.cc
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### Response Timeline

- **Initial Response**: Within 24 hours
- **Triage**: Within 3 business days
- **Fix & Release**: Based on severity (critical issues within 7 days)

### Security Features

The ledger service implements multiple security layers:

#### Cryptographic Security
- Ed25519 signatures via HashiCorp Vault Transit
- SHA256 hashing for data integrity
- Local signature verification
- Rekor transparency log anchoring

#### Input Validation
- Payload size limits
- Subject field validation
- JSON schema validation for metadata
- SQL injection prevention via prepared statements

#### Transport Security
- TLS 1.3 for all external communications
- Certificate-based authentication where applicable
- Secure headers (HSTS, CSP, etc.)

#### Operational Security
- Principle of least privilege
- Secure defaults
- Comprehensive logging
- Rate limiting
- Request timeouts

### Security Best Practices

When deploying the ledger service:

1. **Environment Variables**: Store secrets in secure environment variable systems
2. **TLS**: Always enable TLS in production
3. **Monitoring**: Enable security monitoring and alerting
4. **Updates**: Keep dependencies updated
5. **Backups**: Implement secure backup procedures
6. **Access Control**: Restrict database and Vault access

### Security Contacts

- **General Security**: security@dreamaware.cc
- **Critical Issues**: Create private security advisory on GitHub
- **Sigstore/Rekor Issues**: sigstore-security@googlegroups.com

### Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

(No entries yet - be the first!)

---

**Last Updated**: 2024-01-15  
**Version**: 1.0