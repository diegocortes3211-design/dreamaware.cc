from __future__ import annotations
import re
from typing import List

_PATTERNS = [
    r"ignore (all|any) previous instructions",
    r"pretend to be|simulate developer mode|dev mode",
    r"reveal system prompt|show your prompt",
    r"base64 decode|hex decode this and run",
    r"curl http://|wget http://",
    r"sudo ",
]

def analyze(prompt: str) -> List[str]:
    issues: List[str] = []
    for pat in _PATTERNS:
        if re.search(pat, prompt, flags=re.IGNORECASE):
            issues.append(f"matched pattern: {pat}")
    if len(prompt) > 200000:
        issues.append("prompt too large")
    return issues

def assert_clean(prompt: str) -> None:
    issues = analyze(prompt)
    if issues:
        raise ValueError("prompt_guard blocked unsafe prompt: " + "; ".join(issues))