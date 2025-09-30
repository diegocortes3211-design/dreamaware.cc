from typing import Any, Dict, AsyncIterator, Optional, Callable

class ChatAdapter:
    """Base class for all chat model adapters."""
    name: str = "base"
    capabilities = {
        "tool_calling": True,
        "json_mode": True,
        "vision": False,
        "audio_in": False,
        "audio_out": False,
    }

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
        """
        The main method to interact with a chat model.

        It can operate in two modes:
        1. Non-streaming: Returns a single dictionary with the full response.
        2. Streaming: Returns an async iterator of response chunks.
        """
        raise NotImplementedError("Subclasses must implement the 'chat' method.")