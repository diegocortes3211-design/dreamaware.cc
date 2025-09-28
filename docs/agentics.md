---
id: agentics
title: Agentics Core
---

This module runs a safe loop:
Plan -> Act -> Evaluate -> Propose.

Scope:
- Read only scans and metrics
- Writes reports to logs
- Never mutates code or merges pull requests

How to run locally:
```
python -m services.agentics.orchestrator
```

Outputs:
- logs/agentics/last_report.json
- logs/agentics/proposals_timestamp.json