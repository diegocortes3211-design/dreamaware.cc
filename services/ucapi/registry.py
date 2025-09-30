# Static or DB-backed; can be swapped by Focus Index router
REGISTRY = {
  "gpt-4o-mini": {"adapter":"openai","provider_model":"gpt-4o-mini"},
  "sonnet-latest": {"adapter":"anthropic","provider_model":"claude-3-5-sonnet-20240620"},
  # "local-ollama": {"adapter":"ollama","provider_model":"llama3:instruct"}
}