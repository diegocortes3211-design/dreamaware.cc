import unittest
from unittest.mock import MagicMock, call

from services.agentics.executive import Action, Executive
from services.agentics.self_modify import SelfModifier
from services.agentics.maintenance import MaintenanceAgent


class TestMaintenanceAgent(unittest.TestCase):

    def setUp(self):
        """Set up mock objects for each test."""
        self.mock_executive = MagicMock(spec=Executive)
        self.mock_self_modifier = MagicMock(spec=SelfModifier)
        self.agent = MaintenanceAgent(self.mock_executive, self.mock_self_modifier)

    def test_run_once_full_cycle_generates_patch_plan(self):
        """
        Verify that the agent can generate a plan to apply a patch
        based on a series of simulated executive actions.
        """
        # 1. Setup mock proposal from SelfModifier
        self.mock_self_modifier.propose.return_value = [
            {"title": "Address static analysis findings", "kind": "code"}
        ]

        # 2. Setup mock return value for the initial 'scan_semgrep' action
        mock_semgrep_finding = {
            "ok": True,
            "findings": [{
                "path": "test_file.py",
                "start": {"line": 10},
                "end": {"line": 10},
                "extra": {
                    "message": "Test finding",
                    "lines": "print(\"vulnerable code\")",
                },
                "check_id": "test-rule-id",
            }]
        }

        # 3. Setup mock return value for the subsequent 'read_file' action
        mock_file_content = {
            "ok": True,
            "path": "test_file.py",
            "content": "import os\n\n# ... (some code)\n\nprint(\"vulnerable code\")\n"
        }

        # Configure the mock Executive to return different values on subsequent calls
        self.mock_executive.run.side_effect = [
            # First call to run() is for semgrep
            {"actions": [{"name": "scan_semgrep", "result": mock_semgrep_finding}]},
            # Second call to run() is for reading the file
            {"actions": [{"name": "read_file", "result": mock_file_content}]}
        ]

        # 4. Run the agent's main loop
        result = self.agent.run_once()

        # 5. Assertions
        self.assertEqual(result["status"], "patch_plan_generated")
        self.assertIn("plan", result)

        # Ensure the plan contains an 'apply_patch' action
        self.assertEqual(len(result["plan"]), 1)
        patch_action = result["plan"][0]
        self.assertEqual(patch_action["name"], "apply_patch")
        self.assertIn("patch", patch_action["params"])

        # Check that the generated patch looks reasonable (based on the mock)
        generated_patch = patch_action["params"]["patch"]
        self.assertIn("--- a/test_file.py", generated_patch)
        self.assertIn("+++ b/test_file.py", generated_patch)
        self.assertIn("-print(\"vulnerable code\")", generated_patch)
        self.assertIn("+logger.info(\"This is a mocked fix\")", generated_patch)

        # Verify that the executive was called twice with the correct plans
        self.assertEqual(self.mock_executive.run.call_count, 2)
        first_call_args = self.mock_executive.run.call_args_list[0]
        second_call_args = self.mock_executive.run.call_args_list[1]

        # Check the first call was for semgrep
        self.assertEqual(first_call_args[0][0][0].name, "scan_semgrep")
        # Check the second call was for reading the file
        self.assertEqual(second_call_args[0][0][0].name, "read_file")
        self.assertEqual(second_call_args[0][0][0].params["path"], "test_file.py")


if __name__ == "__main__":
    unittest.main()