#!/usr/bin/env bash
set -euo pipefail
exec uvicorn services.slack.app:app --host 0.0.0.0 --port 8787