from __future__ import annotations
import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncApp
import httpx

# Load secrets from environment variables, raising an error if they're not set.
# This ensures the app fails fast if the environment is not configured correctly.
try:
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
    UCAPI_SERVICE_KEY = os.environ["UCAPI_SERVICE_KEY"]
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e}") from e

# Non-secret configuration with sane defaults
UCAPI_URL = os.getenv("UCAPI_URL", "http://ucapi:8080")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-3-5-sonnet")

# Initialize the Slack App with the bot token and signing secret
bolt = AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
# Initialize the FastAPI app
app = FastAPI()
# Create a request handler for the Slack app
handler = AsyncSlackRequestHandler(bolt)

async def ask_ucapi(prompt: str) -> str:
    """
    Sends a prompt to the UCAPI service and returns the response.
    """
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    headers = {"Authorization": f"Bearer {UCAPI_SERVICE_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{UCAPI_URL}/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "Error: No content found in response.")
        except httpx.RequestError as e:
            # Handle network-related errors
            return f"Error: Could not connect to UCAPI at {e.request.url}."
        except httpx.HTTPStatusError as e:
            # Handle non-2xx responses
            return f"Error: Received status {e.response.status_code} from UCAPI."

@bolt.event("app_mention")
async def on_mention(body, say, logger):
    """Handles mentions of the bot in channels."""
    try:
        text = body.get("event", {}).get("text", "").replace("<@", "").split(">")[-1].strip()
        if not text:
            await say("How can I help you?")
            return
        reply = await ask_ucapi(text)
        await say(reply[:3900])  # Truncate to Slack's message limit
    except Exception as e:
        logger.error(f"Error handling app_mention: {e}")
        await say("Sorry, something went wrong while processing your request.")

@bolt.command("/da")
async def on_da(ack, respond, command):
    """Handles the /da slash command."""
    await ack()
    try:
        query = command.get("text", "").strip() or "hello"
        reply = await ask_ucapi(query)
        await respond(reply[:3900])
    except Exception as e:
        # Using respond here for errors in slash commands is more robust
        await respond(f"Sorry, something went wrong: {e}")

# Expose the Slack event handlers on the FastAPI app
@app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

@app.post("/slack/commands")
async def slack_commands(req: Request):
    return await handler.handle(req)

@app.post("/slack/actions")
async def slack_actions(req: Request):
    return await handler.handle(req)

# To run this app locally:
# uvicorn services.slack.app:app --host 0.0.0.0 --port 8787