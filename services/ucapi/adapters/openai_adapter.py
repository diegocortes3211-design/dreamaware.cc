import os
import json
import httpx
from typing import Any, Dict, Optional, AsyncIterator, Callable

from .base import ChatAdapter

OPENAI_KEY_ENV = "OPENAI_API_KEY"

class OpenAIAdapter(ChatAdapter):
    name = "openai"
    base_url = "https://api.openai.com/v1/chat/completions"

    async def chat(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None,
        tool_choice: str | dict | None,
        params: dict,
        stream: bool,
        stream_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any] | AsyncIterator[Dict[str, Any]]:
        key = os.getenv(OPENAI_KEY_ENV)
        if not key:
            raise RuntimeError(f"{OPENAI_KEY_ENV} is not set.")

        payload = {
            "model": model,
            "messages": messages,
            "temperature": params.get("temperature", 0.2),
            "max_tokens": params.get("max_tokens", 1000),
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            if not stream:
                r = await client.post(self.base_url, headers=headers, json=payload)
                r.raise_for_status()
                return await r.json()
            else:
                if stream_cb is None:
                    raise ValueError("stream_cb must be provided for streaming mode.")

                async def event_stream():
                    async with client.stream("POST", self.base_url, headers=headers, json=payload) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line or not line.startswith("data: "):
                                continue
                            chunk_str = line[6:]
                            if chunk_str == "[DONE]":
                                stream_cb({"event": "message.done"})
                                break

                            try:
                                chunk = json.loads(chunk_str)
                                for choice in chunk.get("choices", []):
                                    delta = choice.get("delta", {})
                                    event = {"event": "message.delta", "delta": delta.get("content")}
                                    if "tool_calls" in delta:
                                        event = {"event": "tool_call.delta", "delta": delta["tool_calls"]}
                                    stream_cb(event)
                                    yield event # also yield the event for direct iteration if needed
                            except json.JSONDecodeError:
                                # Handle cases where a line might not be valid JSON
                                continue

                return event_stream()