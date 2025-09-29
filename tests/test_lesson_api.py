import json
from pathlib import Path
import shutil
from fastapi.testclient import TestClient

# The app needs to be importable
from services.lesson.api import app, LESSONS_DIR

client = TestClient(app)

def setup_function():
    """Create a clean lessons directory before each test."""
    if LESSONS_DIR.exists():
        shutil.rmtree(LESSONS_DIR)
    LESSONS_DIR.mkdir()

def teardown_function():
    """Remove the lessons directory after each test."""
    if LESSONS_DIR.exists():
        shutil.rmtree(LESSONS_DIR)

def test_create_lesson_endpoint():
    """
    Tests the POST /api/lesson endpoint.
    - Asserts a 200 OK response.
    - Verifies that the lesson directory and files are created.
    - Checks that the created lesson.json matches the response.
    """
    # 1. Send a request to create a lesson
    response = client.post(
        "/api/lesson",
        json={"type": "url", "value": "https://example.com/post"},
    )

    # 2. Assert the response is successful
    assert response.status_code == 200
    data = response.json()
    assert data["id"].startswith("lsn_")
    assert len(data["steps"]) == 3

    lesson_id = data["id"]

    # 3. Verify that the directory structure was created
    lesson_dir = LESSONS_DIR / lesson_id
    assert lesson_dir.is_dir()

    lesson_file = lesson_dir / "lesson.json"
    assert lesson_file.is_file()

    steps_dir = lesson_dir / "steps"
    assert steps_dir.is_dir()

    # 4. Verify that the correct number of step files were created
    step_files = list(steps_dir.glob("*.json"))
    assert len(step_files) == 3

    # 5. Verify the content of the main lesson file
    with open(lesson_file, "r") as f:
        lesson_on_disk = json.load(f)

    assert lesson_on_disk["id"] == lesson_id
    assert lesson_on_disk["title"] == "Decoded Lesson Title"
    assert lesson_on_disk["source"]["value"] == "https://example.com/post"
    assert set(lesson_on_disk["steps"]) == set(s.stem for s in step_files)