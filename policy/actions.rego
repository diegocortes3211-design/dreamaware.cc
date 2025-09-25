package actions

default allow = false

# Require explicit minimal permissions and OIDC only
allow {
  input.workflow.permissions.id-token == "write"
  input.workflow.permissions.contents == "read"
}

# Deny granting broad permissions
deny[msg] {
  some k
  v := input.workflow.permissions[k]
  v == "write"
  not k == "id-token"
  msg := sprintf("permission %s:write is not allowed", [k])
}

# Disallow use of repo secrets that look like static AWS creds
deny[msg] {
  some s
  s := input.workflow.secrets[_]
  lower(s) == "aws_access_key_id"  # signal only; we still allow AWS_OIDC_ROLE_ARN (not a secret)
  msg := "static AWS credentials are forbidden; use OIDC"
}

deny[msg] {
  some s
  s := input.workflow.secrets[_]
  lower(s) == "aws_secret_access_key"
  msg := "static AWS credentials are forbidden; use OIDC"
}
