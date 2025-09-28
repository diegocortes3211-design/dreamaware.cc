from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List
import time
from .llm.gemini_client import GeminiClient

PROPOSAL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["proposals"],
    "properties": {
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["target", "change_type", "rationale", "steps"],
                "properties": {
                    "target": {"type": "string"},
                    "change_type": {"type": "string"},
                    "rationale": {"type": "string"},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "expected_effects": {"type": "string"}
                }
            }
        }
    }
}

def make_proposal_prompt(evaluation_json: Dict[str, Any]) -> str:
    return (
        "You are a self improvement engine. Based on the evaluation JSON below, produce proposals that are small, "
        "testable, and safe. Output proposals only as JSON.\n\n"
        f"{json.dumps(evaluation_json, indent=2)}\n"
    )


class SelfModifier:
    """
    Proposes safe, reviewable changes based on evaluation.
    Writes proposals to logs and never mutates code by default.
    """

    def propose(self, evaluation_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        client = GeminiClient()
        prompt = make_proposal_prompt(evaluation_json)
        result = client.generate_json(prompt, PROPOSAL_SCHEMA)
        if result.get("proposals"):
            return result["proposals"]
        # Fallback
        return [{
            "target": "docs",
            "change_type": "improve_documentation",
            "rationale": "no valid llm output",
            "steps": ["add missing readme section on setup"],
            "expected_effects": "improved onboarding"
        }]

    def persist(self, proposals: List[Dict[str, Any]], out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"proposals_{ts}.json"
        path.write_text(json.dumps(proposals, indent=2))
        return path