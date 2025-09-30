from typing import Any, Dict, AsyncIterator, Optional, Callable

from .base import ChatAdapter

class AnthropicAdapter(ChatAdapter):
    name = "anthropic"

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
        # Placeholder for Anthropic API call
        # This will need to be implemented to translate the normalized request
        # to the Anthropic format and normalize the response back.
        raise NotImplementedError("Anthropic adapter is not yet implemented.")