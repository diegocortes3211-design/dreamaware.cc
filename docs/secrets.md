# Secrets Management

This document lists the environment variables required to run the various services in this repository. **Do not commit any secret values to this file or any other file in the repository.**

These secrets should be managed using your deployment platform's secrets management (e.g., Vercel Environment Variables, Render Secret Files, GitHub Secrets for Actions) or a local `.env` file that is listed in `.gitignore`.

## Slack Integration (`services/slack/app.py`)

- `SLACK_BOT_TOKEN`: The bot token for your Slack app (starts with `xoxb-`).
- `SLACK_SIGNING_SECRET`: The signing secret for your Slack app.

## UCAPI Bridge (`services/slack/app.py`)

- `UCAPI_URL`: The base URL for the UCAPI endpoint (e.g., `http://localhost:8080` or a public URL).
- `UCAPI_SERVICE_KEY`: The service key for authenticating with the UCAPI.
- `DEFAULT_MODEL`: (Optional) The default model to use for UCAPI requests. Defaults to `claude-4.5-sonnet`.

## Cursor Pro Adapter (`services/llm_adapters/cursor_pro.py`)

- `CURSOR_API_KEY`: Your API key for the Cursor Pro service.

## General

- `DEFAULT_REPO`: (Optional) The default GitHub repository for integrations that require it.