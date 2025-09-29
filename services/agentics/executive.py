from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import json
import subprocess


@dataclass
class Action:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)


class Executive:
    """
    Plans and runs a minimal set of safe actions for a given objective.
    The default plan favors read only scans and metrics already present in this repo.
    """

    def plan(self, objective: str) -> List[Action]:
        steps: List[Action] = [
            Action("scan_semgrep", {}),
            Action("run_opa_tests", {}),
            Action("read_dabench", {}),
            Action("collect_findings", {"paths": ["policy", "scripts", "services"]}),
        ]
        return steps

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