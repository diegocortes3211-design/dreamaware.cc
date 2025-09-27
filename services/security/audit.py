from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from typing import Any, Dict, Optional

_ROOT = Path(__file__).resolve().parents[2]
_LOGDIR = _ROOT / "logs"
_LOGDIR.mkdir(exist_ok=True)
_LOG = _LOGDIR / "audit.jsonl"

def _hash(text: str) -> str:
    h = hashlib.blake2b(digest_size=16)
    h.update(text.encode("utf-8", "ignore"))
    return h.hexdigest()

def log_event(
    *,
    actor: str,
    task: str,
    provider: str,
    model: str,
    prompt_sample: str = "",
    success: bool,
    latency_ms: Optional[int] = None,
    error: Optional[str] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> None:
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actor": actor,
        "task": task,
        "provider": provider,
        "model": model,
        "prompt_hash": _hash(prompt_sample) if prompt_sample else None,
        "success": success,
        "latency_ms": latency_ms,
        "error": error,
        "extras": extras or {},
    }
    with _LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")