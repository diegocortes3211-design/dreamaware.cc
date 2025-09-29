import os, httpx
from typing import List, Dict, Any, Optional

BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
MODEL_ID = os.getenv("GROK_MODEL_ID", "grok-4-fast-reasoning")
HEADERS = {"Authorization": f"Bearer {os.getenv('GROK_API_KEY')}", "Content-Type": "application/json"}

async def chat(messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.7, stream: bool = False) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": temperature
    }
    # Grok supports OpenAI-style "functions"/"tools" interfaces in many SDKs.
    if tools:
        payload["functions"] = tools
        payload["function_call"] = "auto"

    url = f"{BASE_URL}/chat/completions"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.json()