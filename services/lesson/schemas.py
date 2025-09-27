from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
from datetime import datetime

class Source(BaseModel):
    """Represents the source of a lesson, e.g., a URL or a file."""
    type: Literal["url", "file"]
    value: str

class Lesson(BaseModel):
    """Represents a lesson, which is a sequence of steps."""
    id: str = Field(..., description="Unique identifier for the lesson.")
    source: Source
    title: str
    state: str = Field(..., description="The current state of the lesson in the workflow.")
    steps: List[str] = Field(..., description="An ordered list of step IDs.")
    created_at: datetime

class Step(BaseModel):
    """Represents a single step within a lesson."""
    id: str = Field(..., description="Unique identifier for the step.")
    lesson_id: str
    kind: str = Field(..., description="The type of step (e.g., 'read', 'check').")
    payload: Dict[str, Any] = Field(..., description="The content of the step, which varies by kind.")

class SlopMetrics(BaseModel):
    """Metrics for 'slop' in user-provided text."""
    emoji: int
    emdash: int
    endash: int
    nbsp: int

class AnswerMetrics(BaseModel):
    """Metrics associated with a user's answer."""
    confidence: float = Field(..., ge=0, le=1, description="User's self-reported confidence.")
    slop: SlopMetrics

class AnswerSubmission(BaseModel):
    """Represents a user's submission for a step."""
    step_id: str
    user_choice: int
    free_text: str
    metrics: AnswerMetrics

class SafetyResult(BaseModel):
    """Safety evaluation results from OPA."""
    opa_deny: int

class GradedResult(BaseModel):
    """The result of grading a user's answer submission."""
    ok: bool
    correct_choice: int
    score: float = Field(..., ge=0, le=1)
    explain: str
    safety: SafetyResult