import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

# Environment variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
UCAPI_URL = os.environ.get("UCAPI_URL")
UCAPI_SERVICE_KEY = os.environ.get("UCAPI_SERVICE_KEY")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-4.5-sonnet")

# Initialize Slack Bolt app
if not SLACK_SIGNING_SECRET:
    raise RuntimeError("SLACK_SIGNING_SECRET environment variable not set.")
app = AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
app_handler = AsyncSlackRequestHandler(app)

# Initialize FastAPI app
api = FastAPI()

async def ask_ucapi(prompt: str) -> str:
    """
    Sends a prompt to the UCAPI and returns the assistant's response.
    """
    if not UCAPI_URL or not UCAPI_SERVICE_KEY:
        return "UCAPI is not configured. Please set UCAPI_URL and UCAPI_SERVICE_KEY."

    headers = {"Authorization": f"Bearer {UCAPI_SERVICE_KEY}"}
    payload = {"model": DEFAULT_MODEL, "messages": [{"role": "user", "content": prompt}]}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{UCAPI_URL}/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # Assuming the response has a structure like OpenAI's API
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        return f"Error calling UCAPI: {e.response.status_code} {e.response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@app.event("app_mention")
async def handle_app_mentions(body, say):
    """
    Handles mentions of the bot.
    """
    prompt = body["event"]["text"]
    response_text = await ask_ucapi(prompt)
    await say(text=response_text[:3900])

@app.command("/da")
async def handle_da_command(ack, body, respond):
    """
    Handles the /da slash command.
    """
    await ack()
    prompt = body["text"]
    response_text = await ask_ucapi(prompt)
    await respond(text=response_text)

@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)

@api.post("/slack/commands")
async def slack_commands_endpoint(req: Request):
    return await app_handler.handle(req)

@api.post("/slack/actions")
async def slack_actions_endpoint(req: Request):
    return await app_handler.handle(req)

# To run this app:
# uvicorn services.slack.app:api --host 0.0.0.0 --port 8787