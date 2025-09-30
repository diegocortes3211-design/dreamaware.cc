import os
import httpx
from fastapi import FastAPI, Request
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

# Environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
UCAPI_URL = os.getenv("UCAPI_URL")
UCAPI_SERVICE_KEY = os.getenv("UCAPI_SERVICE_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-3-5-sonnet-20240620")

# Validate that all required environment variables are set
if not all([SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, UCAPI_URL, UCAPI_SERVICE_KEY]):
    raise RuntimeError("Missing one or more required environment variables.")

# Initialize Slack App
bolt_app = AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
app_handler = AsyncSlackRequestHandler(bolt_app)

# Initialize FastAPI App
app = FastAPI()

async def ask_ucapi(prompt: str) -> str:
    """Sends a prompt to the UCAPI service and returns the assistant's response."""
    headers = {"Authorization": f"Bearer {UCAPI_SERVICE_KEY}"}
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{UCAPI_URL}/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Assuming the response has a structure similar to OpenAI's
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            return f"Error communicating with UCAPI: HTTP {e.response.status_code} - {e}"
        except (KeyError, IndexError) as e:
            return f"Error communicating with UCAPI: Invalid response format - {e}"

@bolt_app.event("app_mention")
async def handle_app_mention(body, say):
    """Handles mentions of the bot."""
    prompt = body["event"]["text"]
    response = await ask_ucapi(prompt)
    await say(text=response[:3900])

@bolt_app.command("/da")
async def handle_da_command(ack, command, say):
    """Handles the /da slash command."""
    await ack()
    prompt = command["text"]
    response = await ask_ucapi(prompt)
    await say(text=response)

@app.post("/slack/events")
async def events_endpoint(req: Request):
    return await app_handler.handle(req)

@app.post("/slack/commands")
async def commands_endpoint(req: Request):
    return await app_handler.handle(req)

@app.post("/slack/actions")
async def actions_endpoint(req: Request):
    return await app_handler.handle(req)

# To run this app:
# uvicorn services.slack.app:app --host 0.0.0.0 --port 8787