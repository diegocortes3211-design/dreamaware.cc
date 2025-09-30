import os
import httpx
from typing import List, Dict

CURSOR_API_KEY = os.getenv("CURSOR_API_KEY")

if not CURSOR_API_KEY:
    raise RuntimeError("CURSOR_API_KEY environment variable not set.")

CURSOR_API_URL = "https://api.cursor.com/v1/chat/completions"

async def chat(messages: List[Dict[str, str]]) -> Dict:
    """
    Sends a list of messages to the Cursor chat API.
    """
    headers = {
        "Authorization": f"Bearer {CURSOR_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o", # Or another model supported by Cursor
        "messages": messages,
    }

    # Using a transport with retries for robustness
    transport = httpx.AsyncHTTPTransport(retries=2)
    async with httpx.AsyncClient(transport=transport, timeout=45.0) as client:
        try:
            response = await client.post(CURSOR_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            # Log or handle the error appropriately
            print(f"Error calling Cursor API: {e}")
            raise

async def generate_code(prompt: str) -> str:
    """
    A helper function to generate code using the Cursor API.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates code."},
        {"role": "user", "content": prompt},
    ]
    try:
        response_data = await chat(messages)
        # Assuming a similar response structure to OpenAI
        return response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        return f"Failed to parse Cursor API response: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"