path "transit/*" {
  capabilities = ["create", "read", "update", "list"]
}

path "sys/audit" {
  capabilities = ["read", "list"]
}

path "sys/leases/*" {
  capabilities = ["read", "list"]
}