from __future__ import annotations

from typing import Any, Dict, List

from .executive import Action, Executive
from .self_modify import SelfModifier


class MaintenanceAgent:
    """
    An autonomous agent that proposes, plans, and executes maintenance tasks.
    """

    def __init__(self, executive: Executive, self_modifier: SelfModifier):
        self.executive = executive
        self.self_modifier = self_modifier

    def run_once(self) -> Dict[str, Any]:
        """
        Executes a full cycle: propose -> plan -> execute -> plan for patch.
        """
        # 1. Simulate a prior evaluation to generate proposals
        mock_evaluation = {
            "semgrep_findings": 1, "opa_fail": 0,
            "score": {"utility": 0.5, "safety": 0.8, "cost": 0.5},
        }
        proposals = self.self_modifier.propose(mock_evaluation)

        # 2. Find an actionable proposal
        for proposal in proposals:
            if proposal.get("title") == "Address static analysis findings":
                return self._handle_static_analysis_findings()

        return {"status": "no_actionable_proposals", "plan": []}

    def _handle_static_analysis_findings(self) -> Dict[str, Any]:
        """Orchestrates the process of fixing a static analysis finding."""
        # Stage 1: Scan to find specific issues.
        scan_action = Action("scan_semgrep", {})
        scan_results = self.executive.run([scan_action])
        semgrep_output = scan_results.get("actions", [])[0].get("result", {})
        findings = semgrep_output.get("findings", [])
        if not findings:
            return {"status": "no_findings", "plan": []}

        # Stage 2: Plan and execute reading the affected files.
        read_plan = self._plan_file_reads_from_findings(findings)
        read_results = self.executive.run(read_plan)

        # Stage 3: For each file read, generate a patch.
        patch_plan = self._plan_patches_from_read_results(read_results, findings)

        return {
            "status": "patch_plan_generated",
            "plan": [a.__dict__ for a in patch_plan]
        }

    def _plan_file_reads_from_findings(self, findings: List[Dict[str, Any]]) -> List[Action]:
        """Generates a plan to read files that have findings."""
        plan: List[Action] = []
        read_paths = set()
        for finding in findings:
            file_path = finding.get("path")
            if file_path and file_path not in read_paths:
                plan.append(Action("read_file", {"path": file_path}))
                read_paths.add(file_path)
        return plan

    def _plan_patches_from_read_results(self, read_results: Dict[str, Any], all_findings: List[Dict[str, Any]]) -> List[Action]:
        """Generates a plan to apply patches for each file that was read."""
        patch_plan: List[Action] = []
        for i, action_result in enumerate(read_results.get("actions", [])):
            read_action = action_result.get("name")
            if read_action != "read_file":
                continue

            file_path = action_result.get("result", {}).get("path")
            content = action_result.get("result", {}).get("content")
            if not content:
                continue

            # Find the specific finding associated with this file
            # Note: This simple loop assumes one finding per file for now.
            for finding in all_findings:
                if finding.get("path") == file_path:
                    patch = self._generate_patch(content, finding)
                    if patch:
                        patch_plan.append(Action("apply_patch", {"patch": patch}))
                    break # Move to next file
        return patch_plan

    def _generate_patch(self, file_content: str, finding: Dict[str, Any]) -> str | None:
        """
        Generates a patch to fix a finding. Mocks an LLM call for now.
        """
        prompt = f"""
        Given the following file content and semgrep finding, generate a git-style patch to fix the issue.
        Return ONLY the patch, with no other text or explanation.

        Semgrep finding:
        {finding['extra']['message']}
        Rule ID: {finding['check_id']}
        File: {finding['path']}
        Lines: {finding['start']['line']} - {finding['end']['line']}

        File content:
        ---
        {file_content}
        ---
        """
        # In a real implementation, this would be a call to an LLM.
        # llm_response = self.llm_client.generate(prompt)

        # Mocking a response for a hypothetical simple issue.
        # e.g., replacing 'print("hello")' with 'logger.info("hello")'
        line_to_replace = finding['extra']['lines']
        line_number = finding['start']['line']

        # This is a very simplistic mock patch generator
        patch = f"""--- a/{finding['path']}
+++ b/{finding['path']}
@@ -{line_number},{len(line_to_replace.splitlines())} +{line_number},1 @@
-{line_to_replace.strip()}
+logger.info("This is a mocked fix")
"""
        print(f"Generated Mock Patch:\n{patch}")
        return patch