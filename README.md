![DABench](assets/badges/dabench.svg) ![Coverage](assets/badges/coverage.svg)

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