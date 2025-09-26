package scan.policy

# Import allowlist data
allowlist := input.allowlist

# Main authorization rule
allow {
    # Target must be approved
    target_approved(input.target)
    
    # Profile must be valid
    profile_valid(input.profile)
    
    # Additional constraints for production scans
    production_constraints_met
}

# Check if target matches any approved pattern
target_approved(target) {
    some approved_target
    approved_target := allowlist.approved_targets[_]
    regex.match(approved_target.pattern, target)
}

# Validate scan profile
profile_valid(profile) {
    profile_config := allowlist.scan_profiles[profile]
    profile_config.max_intensity >= 1
}

# Production environment additional constraints
production_constraints_met {
    # Require manual approval for production scans
    input.approval_required == false
}

production_constraints_met {
    # Or if approval is required, check it was granted
    input.approval_required == true
    input.approval_granted == true
}

# Dry run validation (always allowed if target is approved)
allow {
    input.dry_run == true
    target_approved(input.target)
}

# Helper to get profile intensity
profile_intensity(profile) = intensity {
    intensity := allowlist.scan_profiles[profile].max_intensity
}

# Validation for IP addresses
valid_ip(ip) {
    # IPv4 pattern
    regex.match("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", ip)
}

# Validation for hostnames
valid_hostname(hostname) {
    # Basic hostname pattern
    regex.match("^[a-zA-Z0-9][a-zA-Z0-9\\.-]*[a-zA-Z0-9]$", hostname)
}

# Target format validation
target_format_valid(target) {
    valid_ip(target)
}

target_format_valid(target) {
    valid_hostname(target)
}

target_format_valid(target) {
    # CIDR notation
    regex.match("^([0-9]{1,3}\\.){3}[0-9]{1,3}/[0-9]{1,2}$", target)
}

# Comprehensive validation
validate {
    target_format_valid(input.target)
    target_approved(input.target) 
    profile_valid(input.profile)
}