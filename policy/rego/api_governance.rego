package fortress.api

import rego.v1

# API governance policies for Fortress v4
# Controls access to API endpoints and validates request patterns

default allow := false

# API access control
allow if {
	input.method == "POST"
	input.path == "/append"
	valid_auth_header
	rate_limit_ok
}

allow if {
	input.method == "GET"
	input.path in ["/health", "/metrics", "/status"]
}

# Authentication header validation
valid_auth_header if {
	authorization_header := input.headers["Authorization"]
	authorization_header != ""
	startswith(authorization_header, "Bearer ")
}

valid_auth_header if {
	# Allow requests from localhost for development
	input.remote_addr in ["127.0.0.1", "::1"]
}

# Rate limiting
rate_limit_ok if {
	client_id := client_identifier
	current_rate := input.rate_limits[client_id]
	current_rate <= max_requests_per_minute
}

max_requests_per_minute := 60

# Client identification
client_identifier := ip if {
	ip := input.remote_addr
	not input.headers["Authorization"]
}

client_identifier := client_id if {
	auth_header := input.headers["Authorization"]
	client_id := substring(auth_header, 7, -1)  # Remove "Bearer " prefix
}

# CORS validation
cors_allowed if {
	origin := input.headers["Origin"]
	origin in allowed_origins
}

allowed_origins := [
	"http://localhost:3000",
	"http://localhost:5173",
	"https://dreamaware.cc",
	"https://diegocortes3211-design.github.io"
]

# Security headers validation
security_headers_ok if {
	# Ensure dangerous headers are not present
	not input.headers["X-Forwarded-Host"]
	not input.headers["X-Original-URL"]
}

# Request size limits
request_size_ok if {
	content_length := to_number(input.headers["Content-Length"])
	content_length <= 2097152  # 2MB limit
}

request_size_ok if {
	not input.headers["Content-Length"]  # Allow requests without content-length
}

# Policy violations for monitoring
violation[msg] {
	not valid_auth_header
	input.path != "/health"
	input.path != "/metrics"
	input.path != "/status"
	msg := "Missing or invalid authorization header"
}

violation[msg] {
	not rate_limit_ok
	msg := sprintf("Rate limit exceeded: %d requests per minute", [max_requests_per_minute])
}

violation[msg] {
	not cors_allowed
	input.headers["Origin"]
	msg := sprintf("CORS violation: origin %s not allowed", [input.headers["Origin"]])
}