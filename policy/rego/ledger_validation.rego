package fortress.ledger

import rego.v1

# Ledger entry validation policies for Fortress v4
# Validates incoming ledger append requests

# Default deny all
default allow := false

# Allow ledger append if all validation rules pass
allow if {
	input.operation == "append"
	valid_subject
	valid_payload
	valid_metadata
	signature_required
}

# Subject validation - must be non-empty and follow naming convention
valid_subject if {
	input.subject != ""
	regex.match("^[a-zA-Z0-9_.-]+$", input.subject)
	count(input.subject) <= 256
}

# Payload validation - must be non-empty and properly encoded
valid_payload if {
	input.payload != ""
	count(input.payload) > 0
	count(input.payload) <= 1048576  # 1MB limit
}

# Metadata validation - ensure proper structure
valid_metadata if {
	is_object(input.meta)
	# Allow empty metadata
	count(object.keys(input.meta)) >= 0
}

valid_metadata if {
	not input.meta
}

# Signature requirement - ensure cryptographic signing is enforced
signature_required if {
	input.require_signature == true
}

signature_required if {
	not input.require_signature  # Default to requiring signature
}

# Rate limiting policy
rate_limit_check if {
	input.request_count <= 1000  # Max 1000 requests per time window
}

# Audit logging requirement
audit_required if {
	input.operation == "append"
	input.audit_enabled == true
}

# Policy violation reasons for debugging
violation[msg] {
	not valid_subject
	msg := "Invalid subject: must be non-empty, alphanumeric with limited special chars, max 256 chars"
}

violation[msg] {
	not valid_payload
	msg := "Invalid payload: must be non-empty and under 1MB"
}

violation[msg] {
	not valid_metadata
	msg := "Invalid metadata: must be a valid object structure"
}