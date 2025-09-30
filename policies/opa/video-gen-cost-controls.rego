# policies/opa/video-gen-cost-controls.rego
package dreamaware.videogen.cost

import future.keywords.if

# Cost estimation rules
llm_costs := {
    "openai": {"input": 0.000003, "output": 0.000015},      # GPT-4
    "anthropic": {"input": 0.000003, "output": 0.000015},   # Claude Sonnet
    "deepseek": {"input": 0.00000014, "output": 0.00000028} # DeepSeek
}

tts_costs := {
    "edge": {"per_char": 0},           # Free
    "azure": {"per_char": 0.000001},   # Azure Neural
    "openai": {"per_char": 0.000015}   # OpenAI TTS
}

material_costs := {
    "pexels": 0,   # Free
    "pixabay": 0   # Free
}

# Estimate total job cost
estimated_cost := input_cost + output_cost + tts_cost + material_cost

input_cost := input.estimated_tokens.input * llm_costs[input.llm_provider].input
output_cost := input.estimated_tokens.output * llm_costs[input.llm_provider].output
tts_cost := input.script_length * tts_costs[input.tts_provider].per_char
material_cost := count(input.materials) * material_costs["pexels"]

# Per-job budget limit
max_job_cost := 5.0

# User quota enforcement
default allow := false

allow if {
    user_id := input.user_id
    remaining := data.user_quotas[user_id].remaining_usd
    estimated_cost <= remaining
    estimated_cost <= max_job_cost
}

# Emit cost breakdown for transparency
cost_breakdown := {
    "llm": {"input": input_cost, "output": output_cost},
    "tts": tts_cost,
    "materials": material_cost,
    "total": estimated_cost,
    "currency": "USD"
}

# Alert if approaching quota
alert[msg] {
    user_id := input.user_id
    remaining := data.user_quotas[user_id].remaining_usd
    percentage_used := ((data.user_quotas[user_id].total_usd - remaining) / data.user_quotas[user_id].total_usd) * 100
    percentage_used > 80
    msg := sprintf("User %s has used %.1f%% of quota", [user_id, percentage_used])
}