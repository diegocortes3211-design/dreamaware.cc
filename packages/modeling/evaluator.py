from __future__ import annotations
from typing import Iterable, Dict, Any
import math

def perplexity_like(dataset: Iterable[Dict[str, str]]) -> float:
    total = 0
    for item in dataset:
        total += max(1, len(item.get("text", "")))
    # Toy metric for smoke purposes
    return 1000.0 / math.sqrt(total)

def evaluate(dataset: Iterable[Dict[str, str]]) -> Dict[str, Any]:
    ppl = perplexity_like(dataset)
    return {"perplexity_like": round(ppl, 4)}