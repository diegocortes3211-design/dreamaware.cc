from __future__ import annotations
import os, json
from typing import Any, Dict

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")

class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or DEFAULT_MODEL
        self._ready = False
        try:
            import google.generativeai as genai # type: ignore
            if not self.api_key:
                raise RuntimeError("missing api key")
            genai.configure(api_key=self.api_key)
            self._mdl = genai.GenerativeModel(self.model)
            self._ready = True
        except Exception:
            self._ready = False
            self._mdl = None

    def is_ready(self) -> bool:
        return self._ready

    def generate_json(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempts a JSON response. If unavailable, returns {} and caller should fall back.
        """
        if not self._ready:
            return {}
        try:
            # Using plain text generation with schema hint in prompt
            # Keep output fenced as JSON
            sys_prompt = (
                "You are a planner. Output valid JSON that strictly matches the schema below. "
                "No commentary. Only one JSON object."
            )
            schema_hint = json.dumps(response_schema)
            full = f"{sys_prompt}\nSchema:\n{schema_hint}\n\nPrompt:\n{prompt}\n\nJSON:"
            resp = self._mdl.generate_content(full) # type: ignore
            text = resp.text if hasattr(resp, "text") else ""
            # Extract first JSON object
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
        except Exception:
            pass
        return {}