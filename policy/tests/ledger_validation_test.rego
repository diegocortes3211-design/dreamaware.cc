package fortress.ledger

import rego.v1

# Test valid ledger append request
test_valid_append_request if {
	result := allow with input as {
		"operation": "append",
		"subject": "test-subject",
		"payload": "dGVzdCBwYXlsb2Fk",  # base64 encoded "test payload"
		"meta": {"source": "test"},
		"require_signature": true
	}
	result == true
}

# Test invalid subject - empty
test_invalid_empty_subject if {
	result := allow with input as {
		"operation": "append",
		"subject": "",
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {},
		"require_signature": true
	}
	result == false
}

# Test invalid subject - too long
test_invalid_long_subject if {
	long_subject := concat("", array.slice(split(sprintf("%0*s", [300, ""]), ""), 0, 300))
	result := allow with input as {
		"operation": "append", 
		"subject": long_subject,
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {},
		"require_signature": true
	}
	result == false
}

# Test invalid subject - bad characters
test_invalid_subject_chars if {
	result := allow with input as {
		"operation": "append",
		"subject": "test@subject#invalid",
		"payload": "dGVzdCBwYXlsb2Fk", 
		"meta": {},
		"require_signature": true
	}
	result == false
}

# Test valid subject variations
test_valid_subject_variations if {
	result1 := allow with input as {
		"operation": "append",
		"subject": "test-subject_123.v1",
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {},
		"require_signature": true
	}
	
	result2 := allow with input as {
		"operation": "append", 
		"subject": "TestSubject",
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {},
		"require_signature": true
	}
	
	result1 == true
	result2 == true
}

# Test empty payload
test_invalid_empty_payload if {
	result := allow with input as {
		"operation": "append",
		"subject": "test-subject",
		"payload": "",
		"meta": {},
		"require_signature": true
	}
	result == false
}

# Test payload size limit
test_payload_size_limit if {
	# Test just under limit (should pass)
	result1 := allow with input as {
		"operation": "append",
		"subject": "test-subject", 
		"payload": sprintf("%0*s", [1048576, "x"]),  # 1MB
		"meta": {},
		"require_signature": true
	}
	
	# Test over limit (should fail)  
	result2 := allow with input as {
		"operation": "append",
		"subject": "test-subject",
		"payload": sprintf("%0*s", [1048577, "x"]),  # 1MB + 1
		"meta": {},
		"require_signature": true
	}
	
	result1 == true
	result2 == false
}

# Test metadata validation
test_valid_metadata_variations if {
	# Empty metadata
	result1 := allow with input as {
		"operation": "append",
		"subject": "test-subject",
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {},
		"require_signature": true
	}
	
	# Complex metadata
	result2 := allow with input as {
		"operation": "append",
		"subject": "test-subject", 
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {
			"source": "api",
			"version": "1.0",
			"tags": ["important", "test"],
			"timestamp": "2023-12-01T10:00:00Z"
		},
		"require_signature": true
	}
	
	# Missing metadata (should still be valid)
	result3 := allow with input as {
		"operation": "append",
		"subject": "test-subject",
		"payload": "dGVzdCBwYXlsb2Fk", 
		"require_signature": true
	}
	
	result1 == true
	result2 == true
	result3 == true
}

# Test signature requirement
test_signature_requirement if {
	# Explicitly require signature
	result1 := allow with input as {
		"operation": "append",
		"subject": "test-subject",
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {},
		"require_signature": true
	}
	
	# Default should require signature
	result2 := allow with input as {
		"operation": "append", 
		"subject": "test-subject",
		"payload": "dGVzdCBwYXlsb2Fk",
		"meta": {}
	}
	
	result1 == true
	result2 == true
}

# Test violation messages
test_violation_messages if {
	violations := violation with input as {
		"operation": "append",
		"subject": "",
		"payload": "",
		"meta": "invalid"
	}
	
	count(violations) > 0
	"Invalid subject: must be non-empty, alphanumeric with limited special chars, max 256 chars" in violations
	"Invalid payload: must be non-empty and under 1MB" in violations
}