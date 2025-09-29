import json
from pathlib import Path

def get_router_config():
    """Loads the LLM routing configuration."""
    config_path = Path(__file__).resolve().parents[1] / "configs" / "llm_routing.json"
    with open(config_path, "r") as f:
        return json.load(f)

def get_provider_for_task(task_type: str, config: dict) -> str:
    """Simulates the orchestrator's routing logic."""
    return config.get("task_routing", {}).get(task_type)

def test_mega_context_summarize_routes_to_xai():
    """
    Tests that the 'mega_context_summarize' task is correctly routed to the 'xai' provider.
    """
    config = get_router_config()
    provider = get_provider_for_task("mega_context_summarize", config)
    assert provider == "xai"

def test_agent_tooluse_routes_to_xai():
    """
    Tests that the 'agent_tooluse' task is correctly routed to the 'xai' provider.
    """
    config = get_router_config()
    provider = get_provider_for_task("agent_tooluse", config)
    assert provider == "xai"

def test_security_review_routes_to_anthropic():
    """
    Tests that a pre-existing task route remains correct.
    """
    config = get_router_config()
    provider = get_provider_for_task("security_review", config)
    assert provider == "anthropic"