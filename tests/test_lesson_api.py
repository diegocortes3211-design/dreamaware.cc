import json
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

# Make sure the app can be imported
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.lesson.api import app, LESSONS_DIR

client = TestClient(app)

# Define the test fixture path
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_lesson.md"

def setup_function():
    """Create the lessons directory before tests."""
    os.makedirs(LESSONS_DIR, exist_ok=True)

def teardown_function():
    """Clean up the lessons directory after tests."""
    if os.path.exists(LESSONS_DIR):
        shutil.rmtree(LESSONS_DIR)

def test_create_lesson_from_file():
    """
    Tests the POST /api/lesson endpoint by simulating a file upload.
    """
    # 1. Define the source
    source = {"type": "file", "value": str(FIXTURE_PATH)}

    # 2. Make the POST request
    response = client.post("/api/lesson", json=source)

    # 3. Assert the response is successful
    assert response.status_code == 200
    data = response.json()

    # 4. Assert the response contains a valid lesson object
    assert "id" in data
    assert data["id"].startswith("lsn_")
    assert data["source"] == source
    assert "title" in data
    assert data["state"] == "practice"
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0

    # 5. Assert that the created lesson files exist on the filesystem
    lesson_id = data["id"]
    lesson_dir = LESSONS_DIR / lesson_id
    assert lesson_dir.exists()
    assert (lesson_dir / "lesson.json").exists()
    assert (lesson_dir / "steps").exists()

    # Check that step files were created
    num_steps_in_fs = len(list((lesson_dir / "steps").glob("*.json")))
    assert num_steps_in_fs == len(data["steps"])

def test_get_lesson():
    """
    Tests the GET /api/lesson/{lesson_id} endpoint.
    """
    # First, create a lesson to test against
    source = {"type": "url", "value": "https://example.com/test"}
    create_response = client.post("/api/lesson", json=source)
    assert create_response.status_code == 200
    lesson_id = create_response.json()["id"]

    # Now, get the lesson
    get_response = client.get(f"/api/lesson/{lesson_id}")
    assert get_response.status_code == 200
    data = get_response.json()

    assert "lesson" in data
    assert "steps" in data
    assert data["lesson"]["id"] == lesson_id
    assert len(data["steps"]) == len(data["lesson"]["steps"])

def test_submit_answer():
    """
    Tests the POST /api/lesson/{lesson_id}/answer endpoint.
    """
    # Create a lesson
    source = {"type": "url", "value": "https://example.com/test-answer"}
    create_response = client.post("/api/lesson", json=source)
    lesson_id = create_response.json()["id"]
    step_id = create_response.json()["steps"][0] # Get the first step ID

    # Submit an answer for the first step
    submission = {
        "step_id": step_id,
        "user_choice": 1,
        "metrics": {
            "confidence": 0.8,
            "slop": {"emoji": 0, "emdash": 0, "endash": 0, "nbsp": 0},
        },
    }
    answer_response = client.post(f"/api/lesson/{lesson_id}/answer", json=submission)

    assert answer_response.status_code == 200
    result = answer_response.json()
    assert "ok" in result
    assert "correct_choice" in result
    assert "score" in result

    # Check that the answer was logged
    answer_log_file = LESSONS_DIR / lesson_id / "answers.log.jsonl"
    assert answer_log_file.exists()
    with open(answer_log_file, "r") as f:
        log_content = f.read()
        assert step_id in log_content