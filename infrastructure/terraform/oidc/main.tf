terraform {
  required_version = ">= 1.5.0"
  required_providers { aws = { source = "hashicorp/aws", version = ">= 5.0" } }
}

provider "aws" { region = var.aws_region }

# GitHub OIDC provider
data "tls_certificate" "github" { url = "https://token.actions.githubusercontent.com" }

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [for c in data.tls_certificate.github.certificates : c.sha1_fingerprint]
}

# Trust policy: lock to repo + branch (tighten as needed)
data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals { type = "Federated" identifiers = [aws_iam_openid_connect_provider.github.arn] }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.org}/${var.repo}:ref:refs/heads/${var.branch}"]
    }
  }
}

resource "aws_iam_role" "dreamaware_ci" {
  name                 = "DreamAwareCI"
  description          = "OIDC role for GitHub Actions deploys (least privilege)"
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  max_session_duration = 3600
}

# Minimal deploy permissions (optional S3 + CloudFront)
data "aws_iam_policy_document" "deploy" {
  statement {
    sid     = "S3Artifacts"
    actions = ["s3:PutObject","s3:PutObjectAcl","s3:DeleteObject","s3:ListBucket"]
    resources = var.artifact_bucket_arn != "" ? [
      var.artifact_bucket_arn, "${var.artifact_bucket_arn}/*"
    ] : []
    condition { test="Bool" variable="aws:SecureTransport" values=["true"] }
  }
  statement {
    sid      = "CloudFrontInvalidate"
    actions  = ["cloudfront:CreateInvalidation"]
    resources = var.cf_distribution_id != "" ? [
      "arn:aws:cloudfront::*:distribution/${var.cf_distribution_id}"
    ] : []
  }
}

resource "aws_iam_policy" "deploy" {
  name        = "DreamAwareDeployLimited"
  description = "Limited deploy rights for DreamAwareCI"
  policy      = data.aws_iam_policy_document.deploy.json
}

resource "aws_iam_role_policy_attachment" "attach_deploy" {
  role       = aws_iam_role.dreamaware_ci.name
  policy_arn = aws_iam_policy.deploy.arn
}

output "role_arn" {
  description = "Use this ARN in GitHub secrets: AWS_OIDC_ROLE_ARN"
  value       = aws_iam_role.dreamaware_ci.arn
}