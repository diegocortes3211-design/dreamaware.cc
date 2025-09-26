<!-- 
Fortress v4 Pull Request Template

This template ensures adherence to governance guidelines, security checks, and scope constraints.
All sections are required unless marked as optional.
-->

## PR Summary

### Type of Change
<!-- Check all that apply -->
- [ ] 📚 Documentation only
- [ ] 🔧 Configuration/Infrastructure
- [ ] ✨ New feature
- [ ] 🐛 Bug fix
- [ ] 🔒 Security enhancement
- [ ] ♻️ Refactoring
- [ ] 📈 Performance improvement
- [ ] 🧪 Tests

### Description
<!-- Provide a clear and concise description of what this PR does -->


### Related Issues
<!-- Link to related issues using "Fixes #123", "Closes #123", or "Addresses #123" -->
- Fixes #

## Governance Compliance

### Scope Validation
<!-- Confirm your changes align with allowed paths -->
- [ ] Changes are within approved paths (see `tools/policy/paths-allow.json`)
- [ ] No modifications to restricted files (secrets, binaries, critical configs)
- [ ] Documentation changes align with architectural decisions

### Security Checklist
- [ ] No hardcoded secrets or credentials
- [ ] No new external dependencies without security review
- [ ] All new APIs include authentication/authorization
- [ ] Input validation implemented for user-facing changes
- [ ] Security implications assessed and documented

### Architecture Alignment
- [ ] Changes follow Fortress v4 architecture principles
- [ ] Zero-trust principles maintained
- [ ] No new single points of failure introduced
- [ ] Observability and monitoring considered

## Testing and Validation

### Documentation PRs
- [ ] Markdown linting passes (`markdownlint`)
- [ ] Link validation passes (`lychee`)
- [ ] Spelling and grammar reviewed
- [ ] Technical accuracy verified

### Code PRs
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Performance impact assessed
- [ ] Security tests pass (if applicable)

### Infrastructure PRs
- [ ] Changes tested in development environment
- [ ] Rollback procedure documented
- [ ] Security scanning passes
- [ ] Compliance requirements met

## Deployment and Operations

### Deployment Strategy
<!-- How will this be deployed? -->
- [ ] Can be deployed independently
- [ ] Requires coordination with other changes
- [ ] Database migrations included
- [ ] Feature flags configured (if applicable)

### Rollback Plan
<!-- How can this change be rolled back if needed? -->


### Monitoring and Alerting
<!-- What should be monitored after deployment? -->
- [ ] Appropriate metrics/alerts added
- [ ] Dashboard updates included
- [ ] Runbook documentation updated
- [ ] SLI/SLO impact assessed

## Documentation Updates
<!-- Check all that apply -->
- [ ] Architecture docs updated
- [ ] API documentation updated
- [ ] Operational runbooks updated
- [ ] User documentation updated
- [ ] Migration notes added (if applicable)

## Breaking Changes
<!-- Does this introduce breaking changes? -->
- [ ] This PR introduces breaking changes

### If breaking changes, describe:
<!-- Describe the breaking changes and migration path -->


## Additional Context
<!-- Add any additional context, screenshots, or notes -->


## Pre-merge Checklist
<!-- Final checks before merge -->
- [ ] All CI checks pass
- [ ] Code review completed and approved
- [ ] Documentation review completed (if applicable)
- [ ] Security review completed (if required)
- [ ] Deployment plan approved (if required)

---

## For Reviewers

### Review Focus Areas
<!-- Highlight areas that need special attention -->


### Risk Assessment
<!-- Rate the risk level and provide reasoning -->
- Risk Level: [ ] Low [ ] Medium [ ] High
- Reasoning:

### Post-Deployment Verification
<!-- What should be checked after deployment? -->


---

**By submitting this PR, I confirm that:**
- [ ] I have read and understood the contribution guidelines
- [ ] This change aligns with Fortress v4 architectural principles
- [ ] I have tested this change thoroughly
- [ ] I will monitor the deployment and be available for rollback if needed