import os
import asyncio
import httpx
from typing import Dict, Any, List

CURSOR_API_KEY = os.getenv("CURSOR_API_KEY") # Note: Renamed from CURSOR_TOKEN for consistency
CURSOR_BASE = "https://api.cursor.com/v1"

class CursorProAdapter:
    """A simple adapter for the Cursor Pro API."""
    name = "cursor_pro"

    def __init__(self):
        if not CURSOR_API_KEY:
            raise ValueError("CURSOR_API_KEY not set in environment variables")
        self.headers = {
            "Authorization": f"Bearer {CURSOR_API_KEY}",
            "Content-Type": "application/json"
        }

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Sends a chat completion request to the Cursor API."""
        payload = {
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{CURSOR_BASE}/chat/completions", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def generate_code(self, prompt: str, **kwargs) -> str:
        """Generates code using the Cursor API."""
        messages = [{"role": "user", "content": f"Generate code for the following prompt: {prompt}"}]
        response = await self.chat(messages, **kwargs)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def execute_code(self, code: str, **kwargs) -> str:
        """
        Executes code via the Cursor API.
        This is a placeholder for agentic flows, as direct execution might not be a standard API feature.
        """
        messages = [{"role": "user", "content": f"Execute and debug this code, then describe the result: {code}"}]
        response = await self.chat(messages, **kwargs)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")

# Example usage for smoke testing
async def test_cursor_adapter():
    print("Testing CursorProAdapter...")
    try:
        adapter = CursorProAdapter()
        # Mocking a response since we don't have a real key in the test environment
        print("Note: This test will fail without a valid CURSOR_API_KEY. It serves as a structural check.")
        # response = await adapter.generate_code("A simple 'Hello, World!' function in Python")
        # print(f"Response from adapter: {response}")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_cursor_adapter())