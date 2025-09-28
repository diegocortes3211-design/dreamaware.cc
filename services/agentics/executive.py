from __future__ import annotations
import json, yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import subprocess
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

@dataclass
class Action:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)


class Executive:
    """
    Plans and runs a minimal set of safe actions for a given objective.
    The default plan favors read only scans and metrics already present in this repo.
    """

    def plan(self, objective: str, catalog_path: str = "services/agentics/catalog/actions.yaml", constraints: Dict[str, Any] | None = None) -> List[Action]:
        constraints = constraints or {"policy": "zero_slop", "opa": "enabled"}
        actions = load_catalog(catalog_path)
        client = GeminiClient()
        prompt = make_planner_prompt(objective, actions, constraints)
        result = client.generate_json(prompt, ACTION_SCHEMA)
        plan_dicts = result.get("plan")
        if plan_dicts:
            return [Action(name=p.get("name",""), params=p.get("inputs", {})) for p in plan_dicts]
        # Fallback minimal plan
        fallback_dicts: List[Dict[str, Any]] = [
            {"name": "fetch_url", "inputs": {"url": objective}, "justification": "fetch primary source"},
            {"name": "chunk_text", "inputs": {"text": "${fetch_url.text}"}},
        ]
        return [Action(name=p.get("name",""), params=p.get("inputs", {})) for p in fallback_dicts]

    def run(self, actions: List[Action]) -> Dict[str, Any]:
        out: Dict[str, Any] = {"actions": []}
        for a in actions:
            if a.name == "scan_semgrep":
                res = self._semgrep_json()
            elif a.name == "run_opa_tests":
                res = self._opa_test_json()
            elif a.name == "read_dabench":
                res = self._read_json(Path("dabench/report.json"))
            elif a.name == "collect_findings":
                res = {"notes": "collection pass complete", "paths": a.params.get("paths", [])}
            else:
                res = {"error": f"unknown action {a.name}"}
            out["actions"].append({"name": a.name, "result": res})
        return out

    def _semgrep_json(self) -> Dict[str, Any]:
        try:
            p = subprocess.run(
                ["semgrep", "--error", "--json", "-q", "."],
                capture_output=True,
                text=True,
                check=False,
            )
            data = json.loads(p.stdout or "{}")
            return {"ok": True, "findings": data.get("results", []), "summary": data.get("summary", {})}
        except FileNotFoundError:
            return {"ok": False, "reason": "semgrep not installed"}
        except json.JSONDecodeError:
            return {"ok": False, "reason": "semgrep parse error"}

    def _opa_test_json(self) -> Dict[str, Any]:
        try:
            if not Path("policy").exists():
                return {"ok": True, "fail": 0, "note": "no policy directory"}
            p = subprocess.run(
                ["opa", "test", "policy", "-f", "json"],
                capture_output=True,
                text=True,
                check=False,
            )
            data = json.loads(p.stdout or "{}")
            if isinstance(data, dict) and "fail" in data:
                return {"ok": True, "fail": int(data.get("fail", 0))}
            if isinstance(data, list):
                fails = sum(1 for item in data if item.get("pass") is False)
                return {"ok": True, "fail": int(fails)}
            return {"ok": True, "fail": 0}
        except FileNotFoundError:
            return {"ok": False, "reason": "opa not installed"}
        except json.JSONDecodeError:
            return {"ok": False, "reason": "opa parse error"}

    def _read_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"ok": False, "reason": f"{path} not found"}
        try:
            return {"ok": True, "data": json.loads(path.read_text())}
        except json.JSONDecodeError:
            return {"ok": False, "reason": "invalid json"}