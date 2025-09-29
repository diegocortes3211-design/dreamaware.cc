import asyncio
import yaml
from pathlib import Path
import pytest
import sys

# Add the root directory to the path to allow imports from the 'tools' package
sys.path.append(str(Path(__file__).resolve().parents[3]))

from tools.jules.jules_runner import _load_tasks, _toposort, run
from tools.jules.error_memory import _heuristic

@pytest.fixture
def tasks_file(tmp_path: Path) -> Path:
    """Creates a temporary tasks.yaml file for testing."""
    tasks_content = {
        "tasks": [
            {"id": "task_a", "cmd": "echo 'task_a'"},
            {"id": "task_b", "cmd": "echo 'task_b'", "depends": ["task_a"]},
            {"id": "task_c", "cmd": "exit 1"}, # A failing task
        ]
    }
    file_path = tmp_path / "tasks.yaml"
    file_path.write_text(yaml.dump(tasks_content))
    return file_path

def test_load_tasks(tasks_file: Path):
    """Tests that tasks are loaded correctly from the YAML file."""
    tasks = _load_tasks(tasks_file)
    assert len(tasks) == 3
    assert "task_a" in tasks
    assert tasks["task_b"].depends == ["task_a"]

def test_toposort(tasks_file: Path):
    """Tests that the topological sort orders tasks correctly."""
    tasks = _load_tasks(tasks_file)
    sorted_ids = _toposort(tasks)

    assert sorted_ids.index("task_a") < sorted_ids.index("task_b")
    assert "task_c" in sorted_ids

@pytest.mark.asyncio
async def test_orchestrator_run(tmp_path: Path, capsys):
    """
    Tests the main orchestrator 'run' function with a simple success/fail case.
    """
    tasks_content = {
        "tasks": [
            {"id": "success_task", "cmd": "echo 'all good'"},
            {"id": "fail_task", "cmd": "false"}, # This command will fail
        ]
    }
    tasks_file = tmp_path / "tasks.yaml"
    tasks_file.write_text(yaml.dump(tasks_content))

    await run(str(tasks_file), concurrency=2, default_retries=0)

    captured = capsys.readouterr()

    assert "[OK] success_task" in captured.out
    assert "[FAIL] fail_task" in captured.out

    log_dir = Path(".jules/logs")
    assert any(f.name.startswith("success_task") and f.name.endswith(".out") for f in log_dir.iterdir())
    assert any(f.name.startswith("fail_task") and f.name.endswith(".err") for f in log_dir.iterdir())
    assert any(f.name.startswith("fail_task") and f.name.endswith(".advice") for f in log_dir.iterdir())

@pytest.mark.parametrize(
    "stderr, rc, expected_advice",
    [
        ("something something mypy found 2 errors in 1 file", 1, "Mypy found type errors. Run mypy with --show-error-codes to debug."),
        ("main.py:1:1: F401 'os' imported but unused", 1, "Linter error detected. Run the linter with --show-source to see the offending line."),
        ("npm ERR! code ERESOLVE", 1, "NPM dependency conflict. Try running `npm install --legacy-peer-deps` or `npm install --force`."),
        ("npm ERR! 404 Not Found - GET https://registry.npmjs.org/nonexistent-package", 1, "NPM package not found. Check the package name in package.json and ensure the registry is accessible."),
        ("npm ERR! blah blah", 1, "NPM error detected. Check the full log for details (often found in a log file mentioned in the error)."),
        ("some other random error", 1, "Review the log in .jules/logs and re-run; consider enabling debug prints."),
        ("command not found: ruff", 127, "Install the missing command or fix PATH."),
    ]
)
def test_error_heuristics(stderr, rc, expected_advice):
    """Tests the _heuristic function with various error messages."""
    advice = _heuristic(stderr, rc)
    assert advice == expected_advice