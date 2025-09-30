import pytest
from services.ucapi.router import resolve
from services.ucapi.adapters.openai_adapter import OpenAIAdapter
from services.ucapi.adapters.anthropic_adapter import AnthropicAdapter

def test_resolve_valid_openai_model():
    """Tests that a valid OpenAI model alias resolves correctly."""
    adapter, provider_model = resolve("gpt-4o-mini")
    assert isinstance(adapter, OpenAIAdapter)
    assert provider_model == "gpt-4o-mini"

def test_resolve_valid_anthropic_model():
    """Tests that a valid Anthropic model alias resolves correctly."""
    adapter, provider_model = resolve("sonnet-latest")
    assert isinstance(adapter, AnthropicAdapter)
    assert provider_model == "claude-3-5-sonnet-20240620"

def test_resolve_invalid_model():
    """Tests that an invalid model alias raises a ValueError."""
    with pytest.raises(ValueError, match="Model alias 'invalid-model' not found in registry."):
        resolve("invalid-model")

from services.ucapi.registry import REGISTRY

def test_resolve_model_with_unregistered_adapter(monkeypatch):
    """Tests that a model with an unregistered adapter raises a ValueError."""
    # Temporarily add a model to the registry that points to a non-existent adapter
    monkeypatch.setitem(REGISTRY, "new-model", {"adapter": "unregistered", "provider_model": "some-model"})
    with pytest.raises(ValueError, match="Adapter 'unregistered' not found."):
        resolve("new-model")