from __future__ import annotations
import os, time, json, requests
from typing import Any
from ..base import LLMClient, LLMResponse
from ...utils.zero_slop import strip_slop

class AnthropicClient(LLMClient):
    def __init__(self, model: str):
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": int(kwargs.get("max_tokens", 1000)),
            "temperature": float(kwargs.get("temperature", 0.2)),
            "messages": [{"role": "user", "content": strip_slop(prompt)}],
        }
        t0 = time.time()
        resp = requests.post(self.base_url, headers=headers, data=json.dumps(payload), timeout=90)
        dt = int((time.time() - t0) * 1000)
        resp.raise_for_status()
        data = resp.json()
        content = data["content"][0]["text"] if data.get("content") else ""
        usage = data.get("usage", {})
        return LLMResponse(
            text=strip_slop(content),
            model=self.model,
            provider="anthropic",
            latency_ms=dt,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            cost_usd=None,
            raw=data,
        )