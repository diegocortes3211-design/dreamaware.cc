from __future__ import annotations
import os
import json
import requests
import time
from typing import Any, Dict, Protocol, Optional

# Define a common interface
class AIClient(Protocol):
    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]: ...

# Base class for HTTP requests
class _BaseHTTPClient:
    def __init__(self) -> None:
        self._session = requests.Session()
        # Optional mTLS and CA bundle
        ca = os.getenv("CA_BUNDLE_PATH")
        cert = os.getenv("CLIENT_CERT_PATH")
        key = os.getenv("CLIENT_KEY_PATH")
        if ca:
            self._session.verify = ca
        if cert and key:
            self._session.cert = (cert, key)
        self._timeout = int(os.getenv("HTTP_TIMEOUT_SEC", "120"))

    def _post(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._session.post(url, headers=headers, data=json.dumps(payload), timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    def _extract_json(self, text: str) -> Dict[str, Any]:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = text[start_index:end_index + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                raise ValueError("Failed to decode JSON from LLM response.")
        raise ValueError("No valid JSON object found in LLM response.")

# Google Gemini Client
class GeminiClient(_BaseHTTPClient, AIClient):
    def __init__(self, model: str):
        super().__init__()
        self.model = model
        api_key = os.getenv("GOOGLE_API_KEY", "")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        data = self._post(self.url, headers, payload)
        text_content = data["candidates"][0]["content"]["parts"][0]["text"]
        return self._extract_json(text_content)

# OpenAI Client
class OpenAIClient(_BaseHTTPClient, AIClient):
    def __init__(self, model: str):
        super().__init__()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.url = "https://api.openai.com/v1/chat/completions"

    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        data = self._post(self.url, headers, payload)
        text_content = data["choices"][0]["message"]["content"]
        return self._extract_json(text_content)

# Anthropic Claude Client
class ClaudeClient(_BaseHTTPClient, AIClient):
    def __init__(self, model: str):
        super().__init__()
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.url = "https://api.anthropic.com/v1/messages"

    def generate_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system_prompt = "You are a helpful assistant that only returns valid, minified JSON objects. Do not include any text before or after the JSON."
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}]
        }
        data = self._post(self.url, headers, payload)
        text_content = data["content"][0]["text"]
        return self._extract_json(text_content)

# DeepThink placeholder
class DeepThinkClient:
    def __init__(self, model: str): self.model = model
    def generate_text(self, prompt: str, **kwargs: Any) -> LLMResponse:
        # Placeholder for a future API
        text = "DeepThink provider not yet configured."
        return LLMResponse(text=text, provider="deepthink", model=self.model, latency_ms=0)
    def generate_json(self, prompt: str, schema: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return {"error": "deepthink not configured"}