![DABench](assets/badges/dabench.svg)

# dreamaware.ai

AI first. Security driven. Public research and portfolio.

This repository is the home for the dreamaware.ai portal and platform. It includes:

- Docusaurus site under `site/` that serves docs from `docs/`
- Socratic scanning, OPA gating, DABench scoring, race and fuzz jobs
- Commit digest watcher, auto merge label workflow, and badge renderers
- Visualization pipeline that converts specs to assets for the site

## Vision
Build an engineer facing wiki and forum that doubles as a security lab and portfolio. Every change is scanned, reasoned about, and logged. Students and analysts can upload links or files, and the system decodes psychological and cybersecurity signals, then cross links through the somAx engine and color psychology modules.

## Architecture
- Docs and portal: Docusaurus at `site/` with pages sourced from `docs/`
- Socratic analysis: `scripts/socratic_pr.py` plus `prompts/jules.md`
- Policy gate: Rego under `policy/` with tests
- Score and gates: `scripts/dabench_score.py` and `scripts/dabench_gate.py`
- Fuzz jobs: `services/robust/fuzzer.py` with nightly runs
- Visuals as code: specs in `packages/visualization/specs`, renderers in `packages/visualization/renderers`, assets in `site/static/assets/visuals`

## Zero slop policy
- No emojis
- No em dashes or en dashes
- Slop is quantified and flagged in PR reports

## Quick start

### Slack Bridge (Local)

To run the Slack to UCAPI bridge locally, you'll need to set the required environment variables. See `docs/secrets.md` for a full list.

```bash
# Set required secrets (do not commit these values)
export SLACK_BOT_TOKEN="..."
export SLACK_SIGNING_SECRET="..."
export UCAPI_URL="http://localhost:8080" # Or your UCAPI endpoint
export UCAPI_SERVICE_KEY="..."

# Run the bridge
./tools/run_slack_bridge.sh
```

### Deploying the Slack Bridge

To deploy the bridge, you need a public endpoint to provide to Slack. You can use services like Render, Fly.io, or a Cloudflare Tunnel.

1.  Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app.
2.  Choose "From an app manifest" and paste the contents of `services/slack/manifest.yml`.
3.  Update the `request_url` fields in the manifest with your public host URL before creating the app.
4.  Install the app to your workspace and retrieve the Bot Token and Signing Secret.
5.  Set the environment variables in your deployment environment.

### Docusaurus Site

```bash
# Site
cd site
npm ci
npm run build

# Visuals
python packages/visualization/renderers/render_all.py
```

Open `site/build` locally or push to trigger the Pages workflow.

## Roadmap
See `docs/ROADMAP.md` for phase planning and milestones.

## Security
- Static analysis: Semgrep and optional CodeQL
- Policy checks: OPA with purpose and allowlist rules
- Supply chain: SBOM and provenance hooks, to be expanded

## Contributing
Open an issue with the label `autopilot` to let the agent apply safe inline patches. Use `/automerge` and `/noautomerge` on PRs once required checks are set.