from __future__ import annotations
import os, time, json, requests
from typing import Any
from ..base import LLMClient, LLMResponse
from ...utils.zero_slop import strip_slop

class GeminiClientAdapter(LLMClient):
    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": strip_slop(prompt)}]}],
            "generationConfig": {
                "temperature": float(kwargs.get("temperature", 0.2)),
                "maxOutputTokens": int(kwargs.get("max_tokens", 1000)),
            },
        }
        t0 = time.time()
        resp = requests.post(self.base_url, headers=headers, data=json.dumps(payload), timeout=90)
        dt = int((time.time() - t0) * 1000)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return LLMResponse(
            text=strip_slop(text),
            model=self.model,
            provider="gemini",
            latency_ms=dt,
            input_tokens=None,
            output_tokens=None,
            cost_usd=None,
            raw=data,
        )