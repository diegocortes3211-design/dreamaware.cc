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


def get_rag_pipeline_output(source: LessonSource) -> Dict[str, Any]:
    """
    Dummy function to simulate the output of a RAG pipeline.
    In a real implementation, this would involve fetching the source,
    chunking it, and running it through a series of models to
    decode facts and generate questions.
    """
    return {
        "title": f"Decoded Lesson for: {source.value}",
        "steps": [
            {
                "kind": "check",
                "payload": {
                    "question": "Which of the following is a primary color?",
                    "choices": ["Green", "Blue", "Orange", "Violet"],
                    "answer": 1,
                    "context": "Primary colors are red, yellow, and blue.",
                    "sources": ["art_basics.txt#L1"],
                },
            },
            {
                "kind": "explain",
                "payload": {
                    "question": "Why is the sky blue?",
                    "context": "The sky appears blue because of how the Earth's atmosphere scatters sunlight.",
                    "sources": ["physics_for_beginners.md#L42"],
                },
            },
            {
                "kind": "check",
                "payload": {
                    "question": "What is the capital of France?",
                    "choices": ["London", "Berlin", "Paris", "Madrid"],
                    "answer": 2,
                    "context": "Paris is the capital and most populous city of France.",
                    "sources": ["geography.md#L101"],
                },
            },
        ],
    }


@app.post("/api/lesson", response_model=Lesson)
async def create_lesson(source: LessonSource):
    """
    Creates a new lesson from a source using a (simulated) RAG pipeline,
    and saves its structure to the filesystem.
    """
    lesson_id = f"lsn_{uuid.uuid4().hex[:10]}"
    lesson_dir = LESSONS_DIR / lesson_id
    steps_dir = lesson_dir / "steps"
    steps_dir.mkdir(parents=True)

    # Simulate RAG pipeline to get lesson structure
    pipeline_output = get_rag_pipeline_output(source)

    step_ids = []
    for step_data in pipeline_output["steps"]:
        step_id = f"stp_{uuid.uuid4().hex[:10]}"
        step = Step(
            id=step_id,
            lesson_id=lesson_id,
            kind=step_data["kind"],
            payload=StepPayload(**step_data["payload"]),
        )
        with open(steps_dir / f"{step_id}.json", "w") as f:
            json.dump(step.model_dump(), f, indent=2)
        step_ids.append(step_id)

    lesson_data = Lesson(
        id=lesson_id,
        source=source,
        title=pipeline_output["title"],
        state="practice",
        steps=step_ids,
        created_at=dt.datetime.now(dt.UTC).isoformat(),
    )
    with open(lesson_dir / "lesson.json", "w") as f:
        json.dump(lesson_data.model_dump(), f, indent=2)

    return lesson_data


@app.get("/api/lesson/{lesson_id}", response_model=Dict[str, Any])
async def get_lesson(lesson_id: str):
    """
    Retrieves a lesson and all its associated steps from the filesystem.
    """
    lesson_dir = LESSONS_DIR / lesson_id
    lesson_file = lesson_dir / "lesson.json"
    steps_dir = lesson_dir / "steps"

    if not lesson_file.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")

    with open(lesson_file, "r") as f:
        lesson_data = json.load(f)

    steps_data = []
    for step_id in lesson_data.get("steps", []):
        step_file = steps_dir / f"{step_id}.json"
        if step_file.exists():
            with open(step_file, "r") as f:
                steps_data.append(json.load(f))

    return {"lesson": lesson_data, "steps": steps_data}


@app.post("/api/lesson/{lesson_id}/answer", response_model=GradedResult)
async def submit_answer(lesson_id: str, submission: AnswerSubmission):
    """
    Accepts an answer, logs it, and returns a graded result.
    This version performs actual grading against the stored step data.
    """
    lesson_dir = LESSONS_DIR / lesson_id
    step_file = lesson_dir / "steps" / f"{submission.step_id}.json"

    if not step_file.exists():
        raise HTTPException(status_code=404, detail="Step not found")

    with open(step_file, "r") as f:
        step_data = json.load(f)

    # Log the answer
    with open(lesson_dir / "answers.log.jsonl", "a") as f:
        f.write(submission.model_dump_json() + "\n")

    correct_choice = step_data.get("payload", {}).get("answer")
    is_correct = submission.user_choice == correct_choice

    return GradedResult(
        ok=is_correct,
        correct_choice=correct_choice,
        score=1.0 if is_correct else 0.0,
        explain=f"The correct answer was choice {correct_choice + 1}.",
        safety=SafetyResult(opa_deny=0),  # Dummy safety result
    )


@app.post("/api/lesson/{lesson_id}/feedback")
async def submit_feedback(lesson_id: str, feedback: Dict[str, Any]):
    """
    Accepts user feedback for a lesson step and logs it.
    """
    lesson_dir = LESSONS_DIR / lesson_id
    if not lesson_dir.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")

    feedback_log = lesson_dir / "feedback.log.jsonl"
    with open(feedback_log, "a") as f:
        log_entry = {
            "timestamp": dt.datetime.now(dt.UTC).isoformat(),
            "feedback": feedback,
        }
        f.write(json.dumps(log_entry) + "\n")

    return {"queued": True}