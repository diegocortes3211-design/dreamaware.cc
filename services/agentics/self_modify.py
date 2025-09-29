from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json
import time


class SelfModifier:
    """
    Proposes safe, reviewable changes based on evaluation.
    Writes proposals to logs and never mutates code by default.
    """

    def propose(self, evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        props: List[Dict[str, Any]] = []
        score = evaluation.get("score", {})
        safety = float(score.get("safety", 0.0))
        semgrep_findings = int(evaluation.get("semgrep_findings", 0))
        affected_files = int(evaluation.get("affected_files_in_attack_paths", 0))

        if safety < 0.9:
            props.append(
                {
                    "title": "Improve safety gate",
                    "kind": "ci",
                    "summary": "Tune OPA policy and Semgrep rules, raise coverage on risky paths",
                    "impact": "safety",
                }
            )
        if semgrep_findings > 0:
            props.append(
                {
                    "title": "Address static analysis findings",
                    "kind": "code",
                    "summary": "Review Semgrep results and patch flagged files",
                    "impact": "safety",
                }
            )
        if affected_files > 0:
            props.append(
                {
                    "title": "Mitigate predicted attack paths",
                    "kind": "refactor",
                    "summary": f"{affected_files} files are in predicted attack paths. Consider refactoring dependencies to break these chains.",
                    "impact": "safety",
                }
            )
        if not props:
            props.append({"title": "No changes proposed", "kind": "noop", "summary": "", "impact": "none"})
        return props

    def persist(self, proposals: List[Dict[str, Any]], out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"proposals_{ts}.json"
        path.write_text(json.dumps(proposals, indent=2))
        return path