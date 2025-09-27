from __future__ import annotations
import os, time, json, requests
from typing import Any
from ..base import LLMClient, LLMResponse
from ...utils.zero_slop import strip_slop

class GrokClient(LLMClient):
    def __init__(self, model: str, base_url: str | None = None):
        self.model = model
        self.api_key = os.getenv("XAI_API_KEY", "")
        self.base_url = base_url or "https://api.x.ai/v1/chat/completions"

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": strip_slop(prompt)}],
            "temperature": float(kwargs.get("temperature", 0.2)),
            "max_tokens": int(kwargs.get("max_tokens", 1000)),
        }
        t0 = time.time()
        resp = requests.post(self.base_url, headers=headers, data=json.dumps(payload), timeout=90)
        dt = int((time.time() - t0) * 1000)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return LLMResponse(
            text=strip_slop(text),
            model=self.model,
            provider="grok",
            latency_ms=dt,
            raw=data,
        )