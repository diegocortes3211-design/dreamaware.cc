from __future__ import annotations
import json, yaml
from pathlib import Path
from typing import Any, Dict, List
from .llm.gemini_client import GeminiClient

ACTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["plan"],
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "inputs", "justification"],
                "properties": {
                    "name": {"type": "string"},
                    "inputs": {"type": "object"},
                    "justification": {"type": "string"},
                    "expected_outputs": {"type": "array"},
                    "cost_bias": {"type": "string", "enum": ["low", "medium,low", "balanced", "performance"]},
                    "safety_notes": {"type": "string"}
                }
            }
        }
    }
}

def load_catalog(path: str | Path) -> List[Dict[str, Any]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("actions", [])

def make_planner_prompt(objective: str, actions: List[Dict[str, Any]], constraints: Dict[str, Any]) -> str:
    return (
        "Objective:\n"
        f"{objective}\n\n"
        "Action catalog:\n"
        f"{json.dumps(actions, indent=2)}\n\n"
        "Constraints:\n"
        f"{json.dumps(constraints, indent=2)}\n\n"
        "Return JSON with key 'plan' as an ordered list. Each item must reference an action by 'name' "
        "and provide 'inputs' that satisfy the action's inputs schema. Prefer low cost and safe steps. "
        "Do not invent actions not present in the catalog."
    )

def plan(objective: str, catalog_path: str, constraints: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    constraints = constraints or {"policy": "zero_slop", "opa": "enabled"}
    actions = load_catalog(catalog_path)
    client = GeminiClient()
    prompt = make_planner_prompt(objective, actions, constraints)
    result = client.generate_json(prompt, ACTION_SCHEMA)
    if result.get("plan"):
        return result["plan"]
    # Fallback minimal plan
    fallback: List[Dict[str, Any]] = [
        {"name": "fetch_url", "inputs": {"url": objective}, "justification": "fetch primary source"},
        {"name": "chunk_text", "inputs": {"text": "${fetch_url.text}"}},
    ]
    return fallback