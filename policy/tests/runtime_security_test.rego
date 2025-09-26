package fortress.runtime

import rego.v1

# Test memory usage validation
test_memory_usage_validation if {
	# Valid memory usage
	result1 := allow with input as {
		"resource_type": "memory",
		"memory_mb": 256,
		"memory_growth_rate": 0.05
	}
	
	# Exceeds memory limit
	result2 := allow with input as {
		"resource_type": "memory", 
		"memory_mb": 600,
		"memory_growth_rate": 0.05
	}
	
	# Exceeds growth rate limit
	result3 := allow with input as {
		"resource_type": "memory",
		"memory_mb": 256,
		"memory_growth_rate": 0.15
	}
	
	result1 == true
	result2 == false
	result3 == false
}

# Test CPU usage validation
test_cpu_usage_validation if {
	# Valid CPU usage
	result1 := allow with input as {
		"resource_type": "cpu",
		"cpu_percent": 50,
		"cpu_sustained_duration": 120
	}
	
	# Exceeds CPU limit
	result2 := allow with input as {
		"resource_type": "cpu",
		"cpu_percent": 90, 
		"cpu_sustained_duration": 120
	}
	
	# Exceeds sustained duration
	result3 := allow with input as {
		"resource_type": "cpu",
		"cpu_percent": 75,
		"cpu_sustained_duration": 400
	}
	
	result1 == true
	result2 == false
	result3 == false
}

# Test network usage validation
test_network_usage_validation if {
	# Valid network usage
	result1 := allow with input as {
		"resource_type": "network",
		"connections_count": 500,
		"bandwidth_mbps": 50
	}
	
	# Exceeds connection limit
	result2 := allow with input as {
		"resource_type": "network",
		"connections_count": 1200,
		"bandwidth_mbps": 50  
	}
	
	# Exceeds bandwidth limit
	result3 := allow with input as {
		"resource_type": "network",
		"connections_count": 500,
		"bandwidth_mbps": 150
	}
	
	result1 == true
	result2 == false
	result3 == false
}

# Test service health validation
test_service_health if {
	# Healthy service
	result1 := service_healthy with input as {
		"service_status": "running",
		"response_time_ms": 500,
		"error_rate": 0.02
	}
	
	# Unhealthy - not running
	result2 := service_healthy with input as {
		"service_status": "stopped",
		"response_time_ms": 500,
		"error_rate": 0.02
	}
	
	# Unhealthy - slow response
	result3 := service_healthy with input as {
		"service_status": "running", 
		"response_time_ms": 1500,
		"error_rate": 0.02
	}
	
	# Unhealthy - high error rate
	result4 := service_healthy with input as {
		"service_status": "running",
		"response_time_ms": 500,
		"error_rate": 0.1
	}
	
	result1 == true
	result2 == false
	result3 == false
	result4 == false
}

# Test database connection validation
test_database_connections if {
	# Valid DB usage
	result1 := db_connection_ok with input as {
		"db_pool_size": 20,
		"db_active_queries": 30
	}
	
	# Exceeds pool size limit
	result2 := db_connection_ok with input as {
		"db_pool_size": 30,
		"db_active_queries": 30
	}
	
	# Exceeds active queries limit
	result3 := db_connection_ok with input as {
		"db_pool_size": 20,
		"db_active_queries": 60
	}
	
	result1 == true
	result2 == false
	result3 == false
}

# Test WebSocket connection validation  
test_websocket_connections if {
	# Valid WebSocket usage
	result1 := websocket_ok with input as {
		"ws_connections": 500,
		"ws_message_rate": 800
	}
	
	# Exceeds connection limit
	result2 := websocket_ok with input as {
		"ws_connections": 1200,
		"ws_message_rate": 800
	}
	
	# Exceeds message rate limit
	result3 := websocket_ok with input as {
		"ws_connections": 500,
		"ws_message_rate": 1200
	}
	
	result1 == true
	result2 == false
	result3 == false
}

# Test security alerts
test_security_alerts if {
	# Failed auth attempts alert
	result1 := security_alert with input as {
		"failed_auth_attempts": 15,
		"suspicious_patterns": 0,
		"payload_size": 1024
	}
	
	# Suspicious patterns alert
	result2 := security_alert with input as {
		"failed_auth_attempts": 5,
		"suspicious_patterns": 3,
		"payload_size": 1024
	}
	
	# Large payload alert
	result3 := security_alert with input as {
		"failed_auth_attempts": 2,
		"suspicious_patterns": 0,
		"payload_size": 11534336
	}
	
	# No alerts
	result4 := security_alert with input as {
		"failed_auth_attempts": 3,
		"suspicious_patterns": 0,
		"payload_size": 1024
	}
	
	result1 == true
	result2 == true
	result3 == true
	result4 == false
}

# Test performance alerts
test_performance_alerts if {
	# Memory alert
	result1 := performance_alert with input as {
		"memory_mb": 600,
		"memory_growth_rate": 0.05,
		"cpu_percent": 50,
		"response_time_ms": 500
	}
	
	# CPU alert 
	result2 := performance_alert with input as {
		"memory_mb": 300,
		"memory_growth_rate": 0.05,
		"cpu_percent": 90,
		"cpu_sustained_duration": 100,
		"response_time_ms": 500
	}
	
	# Response time alert
	result3 := performance_alert with input as {
		"memory_mb": 300,
		"memory_growth_rate": 0.05,
		"cpu_percent": 50,
		"response_time_ms": 1500
	}
	
	# No alerts
	result4 := performance_alert with input as {
		"memory_mb": 300,
		"memory_growth_rate": 0.05,
		"cpu_percent": 50,
		"response_time_ms": 500
	}
	
	result1 == true
	result2 == true
	result3 == true
	result4 == false
}

# Test violation messages
test_violation_messages if {
	violations := violation with input as {
		"memory_mb": 600,
		"cpu_percent": 90,
		"connections_count": 1200,
		"failed_auth_attempts": 15
	}
	
	count(violations) == 4
	"Memory usage exceeded: 600 MB (limit: 512 MB)" in violations
	"CPU usage exceeded: 90% (limit: 80%)" in violations
	"Network connections exceeded: 1200 (limit: 1000)" in violations
	"Security alert: 15 failed authentication attempts" in violations
}