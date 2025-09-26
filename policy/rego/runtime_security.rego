package fortress.runtime

import rego.v1

# Runtime security and performance policies for Fortress v4
# Monitors and controls system behavior at runtime

default allow := false

# Resource usage policies
allow if {
	input.resource_type == "memory"
	memory_usage_ok
}

allow if {
	input.resource_type == "cpu"
	cpu_usage_ok
}

allow if {
	input.resource_type == "network"
	network_usage_ok
}

# Memory usage validation
memory_usage_ok if {
	input.memory_mb <= max_memory_mb
	input.memory_growth_rate <= max_memory_growth_rate
}

max_memory_mb := 512
max_memory_growth_rate := 0.1  # 10% per minute

# CPU usage validation  
cpu_usage_ok if {
	input.cpu_percent <= max_cpu_percent
	input.cpu_sustained_duration <= max_sustained_duration
}

max_cpu_percent := 80
max_sustained_duration := 300  # 5 minutes

# Network usage validation
network_usage_ok if {
	input.connections_count <= max_connections
	input.bandwidth_mbps <= max_bandwidth
}

max_connections := 1000
max_bandwidth := 100  # 100 Mbps

# Service health validation
service_healthy if {
	input.service_status == "running"
	input.response_time_ms <= max_response_time
	input.error_rate <= max_error_rate
}

max_response_time := 1000  # 1 second
max_error_rate := 0.05     # 5%

# Database connection policies
db_connection_ok if {
	input.db_pool_size <= max_db_connections
	input.db_active_queries <= max_active_queries
}

max_db_connections := 25
max_active_queries := 50

# WebSocket connection policies
websocket_ok if {
	input.ws_connections <= max_ws_connections
	input.ws_message_rate <= max_message_rate
}

max_ws_connections := 1000
max_message_rate := 1000  # messages per second

# Security monitoring
security_alert if {
	input.failed_auth_attempts > 10
}

security_alert if {
	input.suspicious_patterns > 0
}

security_alert if {
	input.payload_size > 10485760  # 10MB
}

# Performance alerts
performance_alert if {
	not memory_usage_ok
}

performance_alert if {
	not cpu_usage_ok
}

performance_alert if {
	input.response_time_ms > max_response_time
}

# Violation reporting
violation[msg] {
	not memory_usage_ok
	msg := sprintf("Memory usage exceeded: %d MB (limit: %d MB)", [input.memory_mb, max_memory_mb])
}

violation[msg] {
	not cpu_usage_ok
	msg := sprintf("CPU usage exceeded: %d%% (limit: %d%%)", [input.cpu_percent, max_cpu_percent])
}

violation[msg] {
	not network_usage_ok
	msg := sprintf("Network connections exceeded: %d (limit: %d)", [input.connections_count, max_connections])
}

violation[msg] {
	security_alert
	input.failed_auth_attempts > 10
	msg := sprintf("Security alert: %d failed authentication attempts", [input.failed_auth_attempts])
}