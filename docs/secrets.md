# Secrets

This document lists the environment variables required for the application to function correctly. These secrets should be stored securely (e.g., in Cursor User/Team Secrets, or your deployment platform's secret management) and should never be hardcoded or committed to the repository.

- `SLACK_BOT_TOKEN`: The bot token for the Slack application.
- `SLACK_SIGNING_SECRET`: The signing secret for the Slack application.
- `UCAPI_URL`: The URL for the UCAPI service.
- `UCAPI_SERVICE_KEY`: The service key for authenticating with the UCAPI service.
- `CURSOR_API_KEY`: The API key for the Cursor service.
- `DEFAULT_MODEL`: The default language model to be used (e.g., `claude-4.5-sonnet`).
- `DEFAULT_REPO`: The default repository for operations (e.g., `diegocortes3211-design/dreamaware.cc`).