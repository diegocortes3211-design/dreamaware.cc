"""
Agentics core package.
This package provides a minimal, safe scaffold for a self improving loop:
Plan -> Act -> Evaluate -> Propose.
Execution never mutates the repo by default. Proposals are written to logs.
"""