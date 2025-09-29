package agent.permissions

# Default: deny
default allow = false

# Allowed capabilities (tighten/expand over time)
allowed_capabilities[c] { c := "biology.query" }
allowed_capabilities[c] { c := "biology.spawn_entity" }
allowed_capabilities[c] { c := "network.access" }
allowed_capabilities[c] { c := "storage.read" }
allowed_capabilities[c] { c := "storage.write" }

# Allow only if every requested capability is in the allowed set
allow {
  input.capabilities
  not exists_disallowed
}

exists_disallowed {
  c := input.capabilities[_]
  not allowed_capabilities[c]
}
