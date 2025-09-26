package fortress.authz

import rego.v1

# Default deny - all access is denied unless explicitly allowed
default allow := false

# Allow access if user is authenticated and has required permissions
allow if {
    # Basic authentication check
    input.user
    input.user.authenticated == true
    
    # Check if user has required role or permission
    has_permission
}

# Permission checking logic
has_permission if {
    # Admin users can access everything
    input.user.role == "admin"
}

has_permission if {
    # Service-to-service authentication
    input.user.type == "service"
    input.user.service_id
    valid_service_permissions
}

has_permission if {
    # Regular users need specific permissions for resources
    input.user.role == "user"
    input.resource
    user_has_resource_permission
}

# Validate service permissions
valid_service_permissions if {
    input.user.service_id in ["fortress-core", "fortress-gateway", "fortress-worker"]
    input.action in ["read", "write", "execute"]
}

# Check user resource permissions
user_has_resource_permission if {
    # Read access to public resources
    input.action == "read"
    input.resource.visibility == "public"
}

user_has_resource_permission if {
    # Full access to owned resources
    input.resource.owner == input.user.id
}

user_has_resource_permission if {
    # Shared resource access
    input.user.id in input.resource.shared_with
    input.action in input.resource.allowed_actions
}

# Rate limiting check
allow if {
    input.user.authenticated == true
    not rate_limited
}

rate_limited if {
    input.rate_limit
    input.rate_limit.current >= input.rate_limit.max
}

# Audit log decision
audit_required if {
    input.action in ["write", "delete", "admin"]
}

audit_required if {
    input.resource.sensitive == true
}