import os
import httpx
from typing import List, Dict, Any

# Read API key from environment
CURSOR_API_KEY = os.environ.get("CURSOR_API_KEY")
CURSOR_API_URL = "https://api.cursor.com/v1/chat/completions"

if not CURSOR_API_KEY:
    raise RuntimeError("CURSOR_API_KEY environment variable not set. This adapter cannot be used.")

# Configure a client with timeouts and retries for robustness
client = httpx.AsyncClient(
    headers={
        "Authorization": f"Bearer {CURSOR_API_KEY}",
        "Content-Type": "application/json"
    },
    timeout=45.0, # Increased timeout for potentially long code generation tasks
    transport=httpx.AsyncHTTPTransport(retries=2)
)

async def chat(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Sends a chat request to the Cursor API.
    """
    payload = {
        "model": "claude-3-opus-20240229", # A powerful model available via Cursor Pro
        "messages": messages
    }
    try:
        response = await client.post(CURSOR_API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Error calling Cursor API: {e.response.status_code} {e.response.text}")
        # Re-raise to allow the caller to handle it
        raise
    except Exception as e:
        print(f"An unexpected error occurred with the Cursor API client: {e}")
        raise

async def generate_code(prompt: str) -> str:
    """
    A helper function to generate code using the Cursor Pro API.
    """
    messages = [
        {"role": "system", "content": "You are an expert code generation assistant. Generate only the code requested by the user, without any extra explanations or markdown fences unless specifically asked."},
        {"role": "user", "content": prompt}
    ]
    try:
        response_data = await chat(messages)
        # Assuming a similar response structure to OpenAI/Anthropic APIs
        return response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"Failed to parse Cursor API response: {e}")
        return "Error: Could not parse the response from the code generation API."
    except Exception:
        # The chat function already prints details, so just return a generic error.
        return "Error: An exception occurred while trying to generate code."