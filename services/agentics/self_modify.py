from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json
import time


class SelfModifier:
    """
    Proposes safe, reviewable changes based on evaluation and Socratic analysis.
    Writes proposals to logs and never mutates code by default.
    """

    def propose(self, evaluation: Dict[str, Any], vuln_maps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        props: List[Dict[str, Any]] = []

        # Generate proposals from vulnerability maps
        for vuln_map in vuln_maps:
            if vuln_map.get("status") == "open":
                props.append(
                    {
                        "title": f"Mitigate Vulnerability in {vuln_map.get('component', 'N/A')}",
                        "kind": "security",
                        "summary": f"Finding: {vuln_map.get('finding', 'N/A')}. Recommended Mitigation: {vuln_map.get('mitigation', 'N/A')}",
                        "impact": vuln_map.get("risk", {}).get("impact", "medium"),
                        "vector": vuln_map.get("vector", "N/A"),
                    }
                )

        # Keep a general safety proposal if the score is low but no specific vulns were mapped.
        score = evaluation.get("score", {})
        safety = float(score.get("safety", 0.0))
        if not props and safety < 0.9:
            props.append(
                {
                    "title": "Improve safety gate",
                    "kind": "ci",
                    "summary": "Safety score is low, but no specific vulnerabilities were mapped. Review OPA policy, Semgrep rules, and test coverage.",
                    "impact": "safety",
                }
            )

        if not props:
            props.append({"title": "No changes proposed", "kind": "noop", "summary": "No open vulnerabilities found and safety score is high.", "impact": "none"})
        return props

    def persist(self, proposals: List[Dict[str, Any]], out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"proposals_{ts}.json"
        path.write_text(json.dumps(proposals, indent=2))
        return path