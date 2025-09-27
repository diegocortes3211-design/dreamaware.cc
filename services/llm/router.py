from __future__ import annotations
from typing import Any, Dict
import yaml
from pathlib import Path
from packages.llmrouter.base import LLMResponse
from packages.llmrouter.adapters.openai_adapter import OpenAIClient
from packages.llmrouter.adapters.anthropic_adapter import AnthropicClient
from packages.llmrouter.adapters.gemini_adapter import GeminiClientAdapter
from packages.llmrouter.adapters.grok_adapter import GrokClient
from packages.utils.zero_slop import strip_slop

_ROOT = Path(__file__).resolve().parents[2]
_CFG = _ROOT / "config" / "models.yaml"

PROVIDERS = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "gemini": GeminiClientAdapter,
    "grok": GrokClient,
}

def _load_cfg() -> Dict[str, Any]:
    if _CFG.exists():
        return yaml.safe_load(_CFG.read_text(encoding="utf-8")) or {}
    return {}

def generate(provider: str, model: str, prompt: str, **kwargs: Any) -> LLMResponse:
    strip = kwargs.pop("strip_slop", True)
    p = strip_slop(prompt) if strip else prompt
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'")
    client = PROVIDERS[provider](model=model)
    return client.generate(p, **kwargs)