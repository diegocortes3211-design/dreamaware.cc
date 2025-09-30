#!/usr/bin/env bash
set -euo pipefail

# This script provides a convenient way to run the Slack bridge locally.
# It ensures that the uvicorn server is started with the correct parameters.
#
# Usage:
# ./tools/run_slack_bridge.sh
#
# Before running, make sure you have set the required environment variables
# as detailed in docs/secrets.md.

echo "Starting Slack bridge..."
exec uvicorn services.slack.app:api --host 0.0.0.0 --port 8787