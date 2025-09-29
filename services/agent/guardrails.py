def sanitize_user_prompt(s: str) -> str:
    # basic injection hardening for tool prompts
    return s.replace("<|", "").replace("|>", "")

# Other guardrails can be added here, such as:
# - Capping tool loops
# - Monitoring token counts
# - Implementing cost dashboards using price hints from limits.yaml