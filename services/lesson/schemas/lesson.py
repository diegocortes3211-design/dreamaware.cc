from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

# Data Contracts from prompt

class LessonSource(BaseModel):
    """Defines the source material for a lesson."""
    type: str
    value: str

class Lesson(BaseModel):
    """Represents a single lesson."""
    id: str
    source: LessonSource
    title: str
    state: str
    steps: List[str]
    created_at: str

class StepPayload(BaseModel):
    """The detailed content of a lesson step."""
    question: str
    choices: Optional[List[str]] = None
    answer: Optional[int] = None
    context: str
    sources: List[str]

class Step(BaseModel):
    """Represents a single step within a lesson."""
    id: str
    lesson_id: str
    kind: Literal["check", "explain", "spot", "read", "reflect"]
    payload: StepPayload

class SlopMetrics(BaseModel):
    """Metrics for 'slop' in free text input."""
    emoji: int
    emdash: int
    endash: int
    nbsp: int

class AnswerMetrics(BaseModel):
    """Metrics associated with a user's answer."""
    confidence: float
    slop: SlopMetrics

class AnswerSubmission(BaseModel):
    """A user's submission for a lesson step."""
    step_id: str
    user_choice: Optional[int] = None
    free_text: Optional[str] = None
    metrics: AnswerMetrics

class SafetyResult(BaseModel):
    """Safety evaluation of an answer."""
    opa_deny: int

class GradedResult(BaseModel):
    """The result of grading a user's answer."""
    ok: bool
    correct_choice: int
    score: float
    explain: str
    safety: SafetyResult