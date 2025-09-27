from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple
import time

@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    latency_ms: int
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None

class LLMClient(Protocol):
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        ...