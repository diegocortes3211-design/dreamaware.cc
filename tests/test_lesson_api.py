import json
from fastapi.testclient import TestClient
from services.lesson.api import app, LESSONS_DIR

client = TestClient(app)

def test_create_lesson():
    # Ensure the lessons directory is clean before test
    if LESSONS_DIR.exists():
        for lesson_dir in LESSONS_DIR.iterdir():
            if lesson_dir.is_dir():
                for f in lesson_dir.glob("**/*"):
                    f.unlink()
                lesson_dir.rmdir()

    # The request payload
    source_payload = {"type": "url", "value": "https://example.com/post"}

    # Make the request
    response = client.post("/api/lesson", json=source_payload)

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Check root level keys
    assert "id" in data
    assert data["id"].startswith("lsn_")
    assert "source" in data
    assert data["source"] == source_payload
    assert "title" in data
    assert "state" in data
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0 # Check that steps were created

    # Check that files were created
    lesson_id = data["id"]
    lesson_dir = LESSONS_DIR / lesson_id
    assert lesson_dir.exists()
    assert (lesson_dir / "lesson.json").exists()

    steps_dir = lesson_dir / "steps"
    assert steps_dir.exists()

    # Verify the step files exist
    for step_id in data["steps"]:
        assert (steps_dir / f"{step_id}.json").exists()

def test_get_lesson():
    # First, create a lesson to test against
    source_payload = {"type": "file", "value": "fixture.md"}
    create_response = client.post("/api/lesson", json=source_payload)
    assert create_response.status_code == 200
    lesson_id = create_response.json()["id"]

    # Now, get the lesson
    get_response = client.get(f"/api/lesson/{lesson_id}")
    assert get_response.status_code == 200
    data = get_response.json()

    assert "lesson" in data
    assert "steps" in data
    assert data["lesson"]["id"] == lesson_id
    assert len(data["steps"]) == len(create_response.json()["steps"])

def test_submit_answer_correct():
    # Create lesson
    create_response = client.post("/api/lesson", json={"type": "text", "value": "..."})
    lesson = create_response.json()
    lesson_id = lesson["id"]

    # Find the 'check' step
    get_response = client.get(f"/api/lesson/{lesson_id}")
    steps = get_response.json()["steps"]
    check_step = next((s for s in steps if s["kind"] == "check"), None)
    assert check_step is not None

    step_id = check_step["id"]
    correct_answer = check_step["payload"]["answer"]

    # Submit correct answer
    answer_payload = {"step_id": step_id, "user_choice": correct_answer}
    response = client.post(f"/api/lesson/{lesson_id}/answer", json=answer_payload)

    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is True
    assert result["score"] == 1.0

def test_submit_answer_incorrect():
    # Create lesson
    create_response = client.post("/api/lesson", json={"type": "text", "value": "..."})
    lesson = create_response.json()
    lesson_id = lesson["id"]

    get_response = client.get(f"/api/lesson/{lesson_id}")
    steps = get_response.json()["steps"]
    check_step = next((s for s in steps if s["kind"] == "check"), None)
    step_id = check_step["id"]
    correct_answer = check_step["payload"]["answer"]
    incorrect_answer = correct_answer + 1 if correct_answer < 2 else 0


    # Submit incorrect answer
    answer_payload = {"step_id": step_id, "user_choice": incorrect_answer}
    response = client.post(f"/api/lesson/{lesson_id}/answer", json=answer_payload)

    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is False
    assert result["score"] == 0.0
    assert result["correct_choice"] == correct_answer