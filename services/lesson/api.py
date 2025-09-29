import json
import uuid
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

# Assuming the schemas are in the adjacent 'schemas' directory
from .schemas.lesson import (
    Lesson,
    LessonSource,
    Step,
    AnswerSubmission,
    GradedResult,
    SafetyResult,
    StepPayload,
)

app = FastAPI(title="Lesson Service API")

# Allow CORS for local development between Docusaurus and this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Docusaurus dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


LESSONS_DIR = Path("lessons")
LESSONS_DIR.mkdir(exist_ok=True)


@app.post("/api/lesson", response_model=Lesson)
async def create_lesson(source: LessonSource):
    """
    Creates a new lesson from a source, generating its structure on the filesystem.
    """
    lesson_id = f"lsn_{uuid.uuid4().hex[:10]}"
    lesson_dir = LESSONS_DIR / lesson_id
    steps_dir = lesson_dir / "steps"
    steps_dir.mkdir(parents=True)

    # Create dummy steps for the v0.1 flow
    step_ids = [f"stp_{uuid.uuid4().hex[:10]}" for _ in range(3)]
    step_files = []
    for i, step_id in enumerate(step_ids):
        step_data = Step(
            id=step_id,
            lesson_id=lesson_id,
            kind="check",
            payload=StepPayload(
                question=f"Sample Question {i+1}: Which claim is unsupported?",
                choices=["Choice A", "Choice B", "Choice C", "Choice D"],
                answer=i % 4,
                context="This is the excerpt for the question.",
                sources=[f"file.md#L{i*10+1}-L{i*10+10}"],
            ),
        )
        with open(steps_dir / f"{step_id}.json", "w") as f:
            json.dump(step_data.model_dump(), f, indent=2)
        step_files.append(step_id)

    # Create the main lesson file
    lesson_data = Lesson(
        id=lesson_id,
        source=source,
        title="Decoded Lesson Title",
        state="practice",
        steps=step_files,
        created_at=dt.datetime.now(dt.UTC).isoformat(),
    )
    with open(lesson_dir / "lesson.json", "w") as f:
        json.dump(lesson_data.model_dump(), f, indent=2)

    return lesson_data


@app.get("/api/lesson/{lesson_id}", response_model=Dict[str, Any])
async def get_lesson(lesson_id: str):
    """
    Retrieves a lesson and all its associated steps.
    """
    lesson_dir = LESSONS_DIR / lesson_id
    lesson_file = lesson_dir / "lesson.json"
    steps_dir = lesson_dir / "steps"

    if not lesson_file.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")

    with open(lesson_file, "r") as f:
        lesson_data = json.load(f)

    steps_data = []
    for step_file in sorted(steps_dir.glob("*.json")):
        with open(step_file, "r") as f:
            steps_data.append(json.load(f))

    return {"lesson": lesson_data, "steps": steps_data}


@app.post("/api/lesson/{lesson_id}/answer", response_model=GradedResult)
async def submit_answer(lesson_id: str, submission: AnswerSubmission):
    """
    Accepts an answer, logs it, and returns a graded result.
    """
    lesson_dir = LESSONS_DIR / lesson_id
    if not lesson_dir.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Append answer to log file
    with open(lesson_dir / "answers.log.jsonl", "a") as f:
        f.write(submission.model_dump_json() + "\n")

    # Return a hardcoded graded result for v0.1
    return GradedResult(
        ok=False,
        correct_choice=2,
        score=0.0,
        explain="This is a mock explanation. Choice B is unsupported.",
        safety=SafetyResult(opa_deny=0),
    )


@app.post("/api/lesson/{lesson_id}/feedback")
async def submit_feedback(lesson_id: str, feedback: Dict[str, Any]):
    """
    Accepts user feedback for a lesson step.
    """
    lesson_dir = LESSONS_DIR / lesson_id
    if not lesson_dir.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")

    # For now, just acknowledge the request
    # In a real implementation, this would append to a moderation queue.
    return {"queued": True}