# Secrets Contract

This document lists the environment variables required to run the services in this repository.
These secrets should **never** be hardcoded or checked into version control. They should be managed through your deployment platform's secret management (e.g., Vercel Environment Variables, GitHub Secrets, Render.com Secret Files).

## Slack to UCAPI Bridge (`services/slack/app.py`)

- `SLACK_BOT_TOKEN`: The bot token for your Slack app, starting with `xoxb-`.
- `SLACK_SIGNING_SECRET`: The signing secret for your Slack app, used to verify requests from Slack.
- `UCAPI_URL`: The base URL for the UCAPI service (e.g., `http://localhost:8080`).
- `UCAPI_SERVICE_KEY`: The bearer token for authenticating with the UCAPI service.
- `DEFAULT_MODEL`: (Optional) The default model to use for UCAPI requests. Defaults to `claude-3-5-sonnet-20240620`.

## Cursor Pro Adapter (`services/llm_adapters/cursor_pro.py`)

- `CURSOR_API_KEY`: Your API key for the Cursor Pro service.

## General

- `DEFAULT_REPO`: (Optional) A default repository for certain agentic operations.