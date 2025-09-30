from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class Tool(BaseModel):
    type: Literal["function"]
    name: str
    description: str
    parameters: Dict[str, Any]


class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[str] = "auto"
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False
    user: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: FunctionCall


class ResponseMessage(BaseModel):
    role: Literal["assistant"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class ChatResponseChoice(BaseModel):
    index: int
    message: ResponseMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    id: str
    created: int
    model: str
    choices: List[ChatResponseChoice]
    usage: Usage


class ErrorDetail(BaseModel):
    type: str
    message: str
    provider_code: Optional[str] = None
    raw: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail