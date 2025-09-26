# Security Policy

## Supported Versions

We are committed to maintaining the security of the DreamAware project. The following versions are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously and appreciate your help in making DreamAware more secure.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities via:

1. **GitHub Security Advisories** (Preferred):
   - Navigate to the repository's Security tab
   - Click "Report a vulnerability"
   - Fill out the private vulnerability report form

2. **Email**: 
   - Send an email to the repository maintainer via GitHub
   - Use the subject line: "[SECURITY] Vulnerability Report for DreamAware"

### What to Include

When reporting a vulnerability, please include:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested mitigation or fix
- Your contact information for follow-up questions

### Response Timeline

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Status Updates**: We will provide regular status updates every 10 business days until resolution
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### Disclosure Policy

- We follow coordinated vulnerability disclosure principles
- We will work with you to understand and fix the issue before public disclosure
- We will credit you in our security advisory (unless you prefer to remain anonymous)
- We ask for your cooperation in not publicly disclosing the issue until we have had a chance to fix it

### Supported Reporting Languages

- English
- Spanish

### Scope

This security policy covers:
- The main DreamAware application codebase
- Dependencies and third-party libraries used in production
- Configuration files and deployment scripts
- CI/CD pipeline security

Out of scope:
- Issues in third-party services or platforms
- Social engineering attacks
- Physical security issues

## Security Measures

This project implements several security measures:

- **Secret Scanning**: Automated detection of credentials and API keys using Gitleaks
- **Static Analysis**: CodeQL security analysis for code vulnerabilities  
- **Content Security Policy**: CSP headers to prevent XSS and other injection attacks
- **Security Headers**: Comprehensive HTTP security headers implementation
- **Dependency Scanning**: Regular dependency vulnerability checks

## Security Contact

For security-related questions or concerns that are not vulnerabilities, you may create a public issue or discussion in the repository.

Thank you for helping keep DreamAware and our users safe!