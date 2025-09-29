from __future__ import annotations
import time
from typing import Any, Dict, List

class SocraticAnalyzer:
    """
    Performs Socratic analysis on evaluation results to generate
    structured Vulnerability Map entries for security findings.
    """

    def analyze(self, exec_output: Dict[str, Any], evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzes evaluation and execution data to produce a list of vulnerability maps.
        For now, it focuses on Semgrep findings.
        """
        vuln_maps = []
        semgrep_action = self._pick_action(exec_output, "scan_semgrep")
        semgrep_findings = (semgrep_action or {}).get("result", {}).get("findings", [])

        if semgrep_findings:
            # Create a single, aggregated vulnerability map for all Semgrep findings.
            # Evidence from the first finding is used as a representative example.
            first_finding = semgrep_findings[0]
            path = first_finding.get("path", "unknown_file")
            start_line = first_finding.get("start", {}).get("line", "N/A")
            component = f"{path}:{start_line}"
            snippet = first_finding.get("extra", {}).get("lines", "")

            vuln_map = {
                "component": component,
                "claim": "The repository should be free of high-risk security vulnerabilities identified by static analysis.",
                "evidence": {
                    "file": path,
                    "lines": str(start_line),
                    "snippet": snippet,
                    "inputs": []  # Not applicable for static analysis findings yet
                },
                "vector": "Security/Static Analysis",
                "risk": {
                    "impact": "medium",  # Default impact for static analysis findings
                    "likelihood": "high",  # High likelihood as the tool flagged it
                    "severity": round(1.0 - evaluation["score"]["safety"], 2)
                },
                "finding": f"Semgrep identified {len(semgrep_findings)} potential issue(s). The first finding is: '{first_finding.get('extra', {}).get('message', 'N/A')}'",
                "mitigation": "Review all static analysis findings and apply necessary code changes to remediate the identified risks.",
                "checks": {
                    "semgrep": [finding.get("check_id", "N/A") for finding in semgrep_findings],
                    "tests": [],
                    "opa": ""
                },
                "dabench": evaluation["score"],
                "provenance": {
                    "commit": "HEAD",  # Placeholder, could be replaced with actual commit hash
                    "pr": 0,  # Placeholder
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                },
                "status": "open"
            }
            vuln_maps.append(vuln_map)

        return vuln_maps

    def _pick_action(self, out: Dict[str, Any], action_name: str) -> Dict[str, Any] | None:
        """Helper to find a specific action's output from the executive summary."""
        for a in out.get("actions", []):
            if a.get("name") == action_name:
                return a
        return None