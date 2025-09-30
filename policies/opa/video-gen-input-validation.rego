# policies/opa/video-gen-input-validation.rego
package dreamaware.videogen.input

import future.keywords.if

# Default deny
default allow := false

# Input sanitization rules
topic_max_length := 500
topic_min_length := 10

# Dangerous patterns that indicate prompt injection
injection_patterns := [
    "ignore previous",
    "ignore all",
    "system:",
    "<|im_start|>",
    "### instruction",
    "[INST]",
    "disregard"
]

# Character whitelist (alphanumeric + basic punctuation)
valid_chars := `^[a-zA-Z0-9\s\.,!?\-'"]+$`

# Validate topic input
allow if {
    topic := input.topic

    # Length check
    count(topic) >= topic_min_length
    count(topic) <= topic_max_length

    # Pattern check
    not contains_injection(topic)

    # Character check
    regex.match(valid_chars, topic)
}

# Helper: detect injection patterns
contains_injection(text) if {
    lower_text := lower(text)
    some pattern in injection_patterns
    contains(lower_text, pattern)
}

# Helper: detect invisible Unicode
contains_invisible_unicode(text) if {
    # Check for zero-width and control characters
    regex.match(`[\u200B-\u200D\uFEFF-\u001F\u007F-\u009F]`, text)
}

# Threat classification
threats[threat] {
    topic := input.topic
    count(topic) > topic_max_length
    threat := "LENGTH_EXCEEDED"
}

threats[threat] {
    contains_injection(input.topic)
    threat := "INJECTION_PATTERN_DETECTED"
}

threats[threat] {
    not regex.match(valid_chars, input.topic)
    threat := "INVALID_CHARACTERS"
}

threats[threat] {
    contains_invisible_unicode(input.topic)
    threat := "INVISIBLE_UNICODE"
}

# Provider selection validation
allowed_llm_providers := {
    "openai",
    "anthropic",
    "deepseek",
    "moonshot"
}

allowed_tts_providers := {
    "edge",
    "azure",
    "openai"
}

allow_provider if {
    input.llm_provider in allowed_llm_providers
    input.tts_provider in allowed_tts_providers
}