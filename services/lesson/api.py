from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# --- Configuration ---
LESSONS_DIR = Path("lessons")
LESSONS_DIR.mkdir(exist_ok=True)

# --- Pydantic Models ---

class LessonSource(BaseModel):
    type: str
    value: str

class Lesson(BaseModel):
    id: str = Field(default_factory=lambda: f"lsn_{uuid.uuid4().hex[:10]}")
    source: LessonSource
    title: str = "Decoded lesson"
    state: str = "practice"
    steps: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class Step(BaseModel):
    id: str = Field(default_factory=lambda: f"stp_{uuid.uuid4().hex[:10]}")
    lesson_id: str
    kind: str
    payload: Dict[str, Any]

class AnswerSubmission(BaseModel):
    step_id: str
    user_choice: int
    free_text: str | None = None
    metrics: Dict[str, Any] | None = None

class GradedResult(BaseModel):
    ok: bool
    correct_choice: int
    score: float
    explain: str
    safety: Dict[str, Any]

class Feedback(BaseModel):
    step_id: str
    label: str
    note: str | None = None


# --- FastAPI App ---
app = FastAPI(title="Lesson API")


# --- Helper Functions ---
def save_lesson(lesson: Lesson):
    lesson_dir = LESSONS_DIR / lesson.id
    lesson_dir.mkdir(exist_ok=True)
    (lesson_dir / "lesson.json").write_text(lesson.model_dump_json(indent=2))

def save_step(step: Step):
    lesson_dir = LESSONS_DIR / step.lesson_id
    steps_dir = lesson_dir / "steps"
    steps_dir.mkdir(exist_ok=True)
    (steps_dir / f"{step.id}.json").write_text(step.model_dump_json(indent=2))

def get_lesson_dir(lesson_id: str) -> Path:
    lesson_dir = LESSONS_DIR / lesson_id
    if not lesson_dir.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson_dir

# --- API Endpoints ---

@app.post("/api/lesson", response_model=Lesson)
async def create_lesson(source: LessonSource):
    """
    Creates a new lesson from a source, generates initial steps, and returns the lesson object.
    """
    # This is a mock implementation. A real implementation would use RAG/LLMs.
    lesson = Lesson(source=source)

    # Generate some mock steps
    step1 = Step(lesson_id=lesson.id, kind="check", payload={
        "question": "Which of these is a fruit?",
        "choices": ["Carrot", "Apple", "Broccoli"],
        "answer": 1,
        "context": "An apple is a sweet, edible fruit produced by an apple tree.",
        "sources": ["source.txt#L1-L2"]
    })
    step2 = Step(lesson_id=lesson.id, kind="explain", payload={
        "prompt": "Explain why an apple is a fruit."
    })

    lesson.steps = [step1.id, step2.id]

    save_lesson(lesson)
    save_step(step1)
    save_step(step2)

    return lesson

@app.get("/api/lesson/{lesson_id}", response_model=Dict)
async def get_lesson(lesson_id: str):
    """
    Retrieves a lesson and its resolved steps.
    """
    lesson_dir = get_lesson_dir(lesson_id)
    lesson_path = lesson_dir / "lesson.json"
    lesson_data = json.loads(lesson_path.read_text())

    steps_data = []
    steps_dir = lesson_dir / "steps"
    if steps_dir.exists():
        for step_file in steps_dir.glob("*.json"):
            steps_data.append(json.loads(step_file.read_text()))

    return {"lesson": lesson_data, "steps": steps_data}

@app.post("/api/lesson/{lesson_id}/answer", response_model=GradedResult)
async def submit_answer(lesson_id: str, submission: AnswerSubmission):
    """
    Accepts an answer, grades it, and returns the result.
    """
    lesson_dir = get_lesson_dir(lesson_id)
    step_path = lesson_dir / "steps" / f"{submission.step_id}.json"
    if not step_path.exists():
        raise HTTPException(status_code=404, detail="Step not found")

    step_data = json.loads(step_path.read_text())

    # Mock grading logic
    correct_answer = step_data.get("payload", {}).get("answer")
    is_correct = submission.user_choice == correct_answer

    result = GradedResult(
        ok=is_correct,
        correct_choice=correct_answer,
        score=1.0 if is_correct else 0.0,
        explain=f"The correct answer was option {correct_answer}.",
        safety={"opa_deny": 0}
    )

    # Append answer to log
    answers_log = lesson_dir / "answers.log.jsonl"
    with answers_log.open("a") as f:
        log_entry = {
            "submission": submission.model_dump(),
            "result": result.model_dump()
        }
        f.write(json.dumps(log_entry) + "\n")

    return result

@app.post("/api/lesson/{lesson_id}/feedback")
async def submit_feedback(lesson_id: str, feedback: Feedback):
    """
    Receives feedback for a step and appends it to a moderation queue.
    """
    get_lesson_dir(lesson_id) # just to validate lesson exists

    feedback_log = LESSONS_DIR / "moderation_queue.log.jsonl"
    with feedback_log.open("a") as f:
        log_entry = {
            "lesson_id": lesson_id,
            "feedback": feedback.model_dump()
        }
        f.write(json.dumps(log_entry) + "\n")

    return {"queued": True}