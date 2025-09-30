from .registry import REGISTRY
from .adapters.base import ChatAdapter
from .adapters.openai_adapter import OpenAIAdapter
from .adapters.anthropic_adapter import AnthropicAdapter

ADAPTERS: dict[str, ChatAdapter] = {
    "openai": OpenAIAdapter(),
    "anthropic": AnthropicAdapter(),
}

def resolve(model_alias: str) -> tuple[ChatAdapter, str]:
    """
    Resolves a model alias to the corresponding adapter instance and provider-specific model name.
    """
    if model_alias not in REGISTRY:
        raise ValueError(f"Model alias '{model_alias}' not found in registry.")

    config = REGISTRY[model_alias]
    adapter_name = config["adapter"]
    provider_model = config["provider_model"]

    if adapter_name not in ADAPTERS:
        raise ValueError(f"Adapter '{adapter_name}' not found.")

    adapter = ADAPTERS[adapter_name]
    return adapter, provider_model