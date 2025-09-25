# AWS OIDC for GitHub Actions

## Why
- No long-lived AWS keys
- Short-lived, scoped STS sessions
- Auditable via CloudTrail

## Setup
1) `cd infrastructure/terraform/oidc`
2) Edit `variables.tf` to set org/repo/branch and (optionally) S3/CloudFront
3) `terraform init && terraform apply`
4) In GitHub → Settings → Secrets and variables → Actions:
   - Add Repository Secret: `AWS_OIDC_ROLE_ARN` = (terraform output role_arn)
5) Protect the `prod` environment and require reviewers.

## Validate
- Open a PR touching `infrastructure/**` → see **Plan** only
- Merge to `main` → **Apply** runs after `prod` env approval
- CloudTrail → look for `AssumeRoleWithWebIdentity` with `token.actions.githubusercontent.com`

## Rollback
- Re-run with previous commit
- Temporarily disable `apply` by removing environment approval (not recommended for long)