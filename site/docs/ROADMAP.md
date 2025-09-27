---
id: roadmap
title: Roadmap
---

## Phase 0 - Hosting and site
- Migrate to Docusaurus under `site/`
- Enable GitHub Pages deployment for `site/build`
- Add docs index and AI futures pages

## Phase 1 - Socratic and policy baseline
- Socratic scanner emits `logs/socratic_pr.md` and `logs/vuln_map.json`
- OPA gate runs on every PR and push
- DABench score and gate enforce utility, safety, and cost bars

## Phase 2 - Fuzz and bounty lab
- Nightly text and vision fuzz jobs
- Crash artifacts uploaded and logged
- Hook for bounty export to be added

## Phase 3 - Wiki and forum foundation
- MDX wiki pages under `docs/`
- Forum service design and auth plan
- Moderation pipeline that uses the same OPA rules

## Phase 4 - Visualization pipeline
- Specs in `packages/visualization/specs`
- Render to `site/static/assets/visuals` in CI
- Embed visuals in docs with stable links

## Phase 5 - Orchestrator and dashboards
- Composite actions for apply patch, OPA, automerge, digest, external hooks
- Pages with dashboards for findings and trends

## Ongoing
- Zero slop enforcement
- Regular prediction updates under AI futures