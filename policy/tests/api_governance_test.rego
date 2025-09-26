package fortress.api

import rego.v1

# Test valid API requests
test_valid_post_request if {
	result := allow with input as {
		"method": "POST",
		"path": "/append", 
		"headers": {"Authorization": "Bearer test-token"},
		"remote_addr": "192.168.1.100",
		"rate_limits": {"test-token": 30}
	}
	result == true
}

# Test valid GET requests to public endpoints
test_valid_get_requests if {
	result1 := allow with input as {
		"method": "GET",
		"path": "/health",
		"headers": {},
		"remote_addr": "192.168.1.100"
	}
	
	result2 := allow with input as {
		"method": "GET", 
		"path": "/metrics",
		"headers": {},
		"remote_addr": "192.168.1.100"
	}
	
	result3 := allow with input as {
		"method": "GET",
		"path": "/status", 
		"headers": {},
		"remote_addr": "192.168.1.100"
	}
	
	result1 == true
	result2 == true
	result3 == true
}

# Test localhost authentication bypass
test_localhost_bypass if {
	result1 := allow with input as {
		"method": "POST",
		"path": "/append",
		"headers": {},
		"remote_addr": "127.0.0.1",
		"rate_limits": {"127.0.0.1": 10}
	}
	
	result2 := allow with input as {
		"method": "POST", 
		"path": "/append",
		"headers": {},
		"remote_addr": "::1",
		"rate_limits": {"::1": 5}
	}
	
	result1 == true
	result2 == true
}

# Test invalid authentication
test_invalid_auth if {
	# Missing auth header
	result1 := allow with input as {
		"method": "POST",
		"path": "/append",
		"headers": {},
		"remote_addr": "192.168.1.100"
	}
	
	# Invalid auth header format
	result2 := allow with input as {
		"method": "POST",
		"path": "/append", 
		"headers": {"Authorization": "Basic dGVzdA=="},
		"remote_addr": "192.168.1.100"
	}
	
	# Empty auth header
	result3 := allow with input as {
		"method": "POST",
		"path": "/append",
		"headers": {"Authorization": ""},
		"remote_addr": "192.168.1.100"
	}
	
	result1 == false
	result2 == false
	result3 == false
}

# Test rate limiting
test_rate_limiting if {
	# Under rate limit
	result1 := allow with input as {
		"method": "POST",
		"path": "/append",
		"headers": {"Authorization": "Bearer test-token"},
		"remote_addr": "192.168.1.100",
		"rate_limits": {"test-token": 50}
	}
	
	# Over rate limit
	result2 := allow with input as {
		"method": "POST",
		"path": "/append",
		"headers": {"Authorization": "Bearer test-token"},
		"remote_addr": "192.168.1.100", 
		"rate_limits": {"test-token": 70}
	}
	
	result1 == true
	result2 == false
}

# Test client identification
test_client_identification if {
	# IP-based identification (no auth)
	client1 := client_identifier with input as {
		"remote_addr": "192.168.1.100",
		"headers": {}
	}
	
	# Token-based identification
	client2 := client_identifier with input as {
		"remote_addr": "192.168.1.100", 
		"headers": {"Authorization": "Bearer user-token-123"}
	}
	
	client1 == "192.168.1.100"
	client2 == "user-token-123"
}

# Test CORS validation
test_cors_validation if {
	# Allowed origin
	result1 := cors_allowed with input as {
		"headers": {"Origin": "http://localhost:3000"}
	}
	
	# Another allowed origin
	result2 := cors_allowed with input as {
		"headers": {"Origin": "https://dreamaware.cc"}
	}
	
	# Disallowed origin  
	result3 := cors_allowed with input as {
		"headers": {"Origin": "https://evil.com"}
	}
	
	result1 == true
	result2 == true
	result3 == false
}

# Test security headers validation
test_security_headers if {
	# Safe request
	result1 := security_headers_ok with input as {
		"headers": {
			"Content-Type": "application/json",
			"Authorization": "Bearer test"
		}
	}
	
	# Dangerous headers present
	result2 := security_headers_ok with input as {
		"headers": {
			"X-Forwarded-Host": "evil.com",
			"Authorization": "Bearer test"
		}
	}
	
	result3 := security_headers_ok with input as {
		"headers": {
			"X-Original-URL": "http://evil.com/admin", 
			"Authorization": "Bearer test"
		}
	}
	
	result1 == true
	result2 == false
	result3 == false
}

# Test request size limits
test_request_size_limits if {
	# Valid size
	result1 := request_size_ok with input as {
		"headers": {"Content-Length": "1024"}
	}
	
	# Too large
	result2 := request_size_ok with input as {
		"headers": {"Content-Length": "3145728"}  # 3MB
	}
	
	# No content-length header (should be allowed)
	result3 := request_size_ok with input as {
		"headers": {}
	}
	
	result1 == true
	result2 == false
	result3 == true
}

# Test policy violations
test_policy_violations if {
	violations := violation with input as {
		"method": "POST",
		"path": "/append",
		"headers": {"Origin": "https://evil.com"},
		"remote_addr": "192.168.1.100",
		"rate_limits": {"192.168.1.100": 100}
	}
	
	count(violations) > 0
	"Missing or invalid authorization header" in violations
	"CORS violation: origin https://evil.com not allowed" in violations
}