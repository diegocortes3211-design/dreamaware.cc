from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Score:
    utility: float
    safety: float
    cost: float


class Evaluator:
    """
    Converts raw action outputs into a simple score and a summary.
    Mirrors DABench dimensions when available and falls back to heuristics.
    """

    def evaluate(self, exec_output: Dict[str, Any]) -> Dict[str, Any]:
        semgrep = self._pick(exec_output, "scan_semgrep")
        opa = self._pick(exec_output, "run_opa_tests")
        dabench = self._pick(exec_output, "read_dabench")
        attack_paths_res = self._pick(exec_output, "predict_attack_paths")

        # Calculate penalty from predicted attack paths
        num_affected_files = 0
        if attack_paths_res and attack_paths_res.get("ok"):
            predicted_paths = attack_paths_res.get("predicted_paths", {})
            # Sum the lengths of all path lists to get the total number of affected files
            num_affected_files = sum(len(paths) for paths in predicted_paths.values())

        attack_path_penalty = 0.01 * num_affected_files

        if dabench and dabench.get("ok") and isinstance(dabench.get("data"), dict):
            scores = dabench["data"].get("scores", {})
            base_safety = float(scores.get("safety", 0.0))
            s = Score(
                float(scores.get("utility", 0.0)),
                max(0.0, base_safety - attack_path_penalty),
                float(scores.get("cost", 1.0)),
            )
        else:
            semgrep_findings = len((semgrep or {}).get("findings", []))
            opa_fail = int((opa or {}).get("fail", 0))
            heuristic_safety = 1.0 - 0.03 * semgrep_findings - 0.10 * opa_fail
            s = Score(
                utility=0.5,
                safety=max(0.0, heuristic_safety - attack_path_penalty),
                cost=0.5,
            )

        summary = {
            "semgrep_findings": len((semgrep or {}).get("findings", [])),
            "opa_fail": int((opa or {}).get("fail", 0)),
            "affected_files_in_attack_paths": num_affected_files,
            "score": {"utility": s.utility, "safety": s.safety, "cost": s.cost},
        }
        return summary

    def _pick(self, out: Dict[str, Any], action_name: str) -> Dict[str, Any] | None:
        for a in out.get("actions", []):
            if a.get("name") == action_name:
                return a.get("result")
        return None