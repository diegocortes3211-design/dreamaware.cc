import asyncio
import yaml
from pathlib import Path
import pytest

# Since the runner is in a sibling directory, we adjust the path
import sys
sys.path.append(str(Path(__file__).resolve().parents[3]))

from tools.jules.jules_runner import _load_tasks, _toposort, run

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

    # task_a must come before task_b
    assert sorted_ids.index("task_a") < sorted_ids.index("task_b")
    # task_c has no dependencies, its position is not guaranteed relative to a/b
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

    # Run the orchestrator
    await run(str(tasks_file), concurrency=2, default_retries=0)

    # Capture the output to verify results
    captured = capsys.readouterr()

    # Check that the output indicates success and failure correctly
    assert "[OK] success_task" in captured.out
    assert "[FAIL] fail_task" in captured.out

    # Check that log files were created
    log_dir = Path(".jules/logs")
    assert any(f.name.startswith("success_task") and f.name.endswith(".out") for f in log_dir.iterdir())
    assert any(f.name.startswith("fail_task") and f.name.endswith(".err") for f in log_dir.iterdir())
    assert any(f.name.startswith("fail_task") and f.name.endswith(".advice") for f in log_dir.iterdir())