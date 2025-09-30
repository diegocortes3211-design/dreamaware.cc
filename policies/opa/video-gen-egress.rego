# policies/opa/video-gen-egress.rego
package dreamaware.videogen.egress

import future.keywords.if
import future.keywords.in

# Default deny all egress
default allow := false

# Extract SPIFFE ID from connection metadata
spiffe_id := input.attributes.source.principal

# Extract destination from request
destination_host := input.attributes.request.http.host
destination_path := input.attributes.request.http.path

# Allow list of external APIs by purpose
allowed_destinations := {
    "script_generation": {
        "api.openai.com",
        "api.anthropic.com",
        "api.deepseek.com",
        "api.moonshot.cn"
    },
    "material_sourcing": {
        "api.pexels.com",
        "pixabay.com"
    },
    "voice_synthesis": {
        "speech.platform.bing.com",  # Edge TTS
        "api.openai.com",              # OpenAI TTS
        "cognitiveservices.azure.com"  # Azure Cognitive Services
    }
}

# Service to purpose mapping (from SPIFFE ID)
service_purpose[purpose] {
    contains(spiffe_id, "llm-service")
    purpose := "script_generation"
}

service_purpose[purpose] {
    contains(spiffe_id, "materials-service")
    purpose := "material_sourcing"
}

service_purpose[purpose] {
    contains(spiffe_id, "voice-service")
    purpose := "voice_synthesis"
}

# Allow egress if destination matches service purpose
allow if {
    some purpose in service_purpose
    some allowed_host in allowed_destinations[purpose]
    contains(destination_host, allowed_host)
}

# Rate limiting: max requests per minute per service
request_limit := 100

allow if {
    input.attributes.request.http.method == "GET"
    destination_host == "api.pexels.com"
    check_rate_limit(spiffe_id, request_limit)
}

# Cost limiting: deny if job has exceeded budget
allow if {
    job_id := input.attributes.request.http.headers["x-job-id"]
    job_id != null
    job_cost := data.crdb.jobs[job_id].actual_cost_usd
    job_cost < 5.0  # Max $5 per job
}

# Helper: check rate limit (integrates with external rate limiter)
check_rate_limit(id, limit) {
    # This would call out to Redis or similar
    # Simplified for demonstration
    count(input.attributes.metadataContext.filterMetadata["envoy.filters.http.ratelimit"]) < limit
}

# Audit logging: emit detailed event for every decision
audit_event := {
    "spiffe_id": spiffe_id,
    "destination": destination_host,
    "path": destination_path,
    "purpose": service_purpose,
    "allowed": allow,
    "timestamp": time.now_ns(),
    "request_id": input.attributes.request.http.headers["x-request-id"]
}

# Security violations trigger alerts
violation[msg] {
    not allow
    msg := sprintf("EGRESS DENIED: %s attempted to reach %s (purpose: %v)", [
        spiffe_id,
        destination_host,
        service_purpose
    ])
}