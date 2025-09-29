import json
import jsonschema
from pathlib import Path

from services.agentics.socratic import SocraticAnalyzer

def load_schema():
    """Loads the vulnerability map JSON schema."""
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "vuln_map.schema.json"
    with open(schema_path, "r") as f:
        return json.load(f)

def test_socratic_analyzer_with_semgrep_findings():
    """
    Tests that the SocraticAnalyzer generates a valid vulnerability map
    when semgrep findings are present in the execution output.
    """
    analyzer = SocraticAnalyzer()
    schema = load_schema()

    # Mock data mimicking the output from the executive and evaluator
    mock_exec_output = {
        "actions": [
            {
                "name": "scan_semgrep",
                "result": {
                    "ok": True,
                    "findings": [
                        {
                            "check_id": "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true",
                            "path": "services/utils/runner.py",
                            "start": {"line": 42},
                            "extra": {
                                "message": "Subprocess call with shell=True seems safe, but may be insecure if command is constructed from user input.",
                                "lines": "subprocess.run(cmd, shell=True)"
                            }
                        }
                    ],
                    "summary": {"errors": 0}
                }
            }
        ]
    }
    mock_evaluation = {
        "semgrep_findings": 1,
        "opa_fail": 0,
        "score": {"utility": 0.5, "safety": 0.97, "cost": 0.5}
    }

    vuln_maps = analyzer.analyze(mock_exec_output, mock_evaluation)

    # Assert that one vulnerability map was created
    assert len(vuln_maps) == 1
    vuln_map = vuln_maps[0]

    # Validate the generated map against our schema
    jsonschema.validate(instance=vuln_map, schema=schema)

    # Assert specific fields to ensure logic is correct
    assert vuln_map["component"] == "services/utils/runner.py:42"
    assert vuln_map["vector"] == "Security/Static Analysis"
    assert vuln_map["risk"]["severity"] == 0.03
    assert "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true" in vuln_map["checks"]["semgrep"]
    assert vuln_map["status"] == "open"

def test_socratic_analyzer_no_findings():
    """
    Tests that the SocraticAnalyzer returns an empty list when no
    findings are present.
    """
    analyzer = SocraticAnalyzer()

    mock_exec_output = {
        "actions": [{"name": "scan_semgrep", "result": {"ok": True, "findings": [], "summary": {}}}]
    }
    mock_evaluation = {
        "semgrep_findings": 0,
        "opa_fail": 0,
        "score": {"utility": 0.5, "safety": 1.0, "cost": 0.5}
    }

    vuln_maps = analyzer.analyze(mock_exec_output, mock_evaluation)

    assert len(vuln_maps) == 0