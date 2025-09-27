from __future__ import annotations
from typing import Any, Dict, Optional, Tuple, List
from pathlib import Path
import time
import yaml
from .clients import OpenAIClient, ClaudeClient, GeminiClient, AIClient
from services.security.audit import log_event

_ROOT = Path(__file__).resolve().parents[2]
_CFG = _ROOT / "configs" / "ai_providers.yaml"

_MAP = {
    "openai": OpenAIClient,
    "anthropic": ClaudeClient,  # Anthropic Claude
    "gemini": GeminiClient,
}

def _load_cfg() -> Dict[str, Any]:
    if _CFG.exists():
        return yaml.safe_load(_CFG.read_text(encoding="utf-8")) or {}
    return {}

def get_client(provider: Optional[str] = None, model: Optional[str] = None) -> AIClient:
    cfg = _load_cfg()
    if not provider:
        provider = cfg.get("default", {}).get("provider", "gemini")
    if not model:
        model = cfg.get("default", {}).get("model", "gemini-1.5-pro")
    if provider not in _MAP:
        raise ValueError(f"unknown provider {provider}")
    return _MAP[provider](model=model)

def choose_for_task(task: str) -> Tuple[str, str]:
    cfg = _load_cfg()
    if task == "short_json":
        p = cfg.get("routes", {}).get("short_json", {"provider": "openai", "model": "gpt-4o-mini"})
        return p["provider"], p["model"]
    if task == "long_doc":
        p = cfg.get("routes", {}).get("long_doc", {"provider": "gemini", "model": "gemini-1.5-pro"})
        return p["provider"], p["model"]
    if task == "code":
        p = cfg.get("routes", {}).get("code", {"provider": "anthropic", "model": "claude-3-5-sonnet"})
        return p["provider"], p["model"]
    d = cfg.get("default", {"provider": "gemini", "model": "gemini-1.5-pro"})
    return d["provider"], d["model"]

# simple in-memory circuit breaker
_CB: Dict[Tuple[str, str], Dict[str, float]] = {}
_MAX_FAILS = int((os.environ.get("CB_MAX_FAILS") or "3"))
_RESET_SEC = int((os.environ.get("CB_RESET_SEC") or "120"))

def _circuit_open(p: str, m: str) -> bool:
    st = _CB.get((p, m))
    if not st:
        return False
    if st.get("fail_count", 0) < _MAX_FAILS:
        return False
    return time.time() < st.get("open_until", 0)

def _record_fail(p: str, m: str) -> None:
    st = _CB.setdefault((p, m), {"fail_count": 0, "open_until": 0})
    st["fail_count"] = st.get("fail_count", 0) + 1
    if st["fail_count"] >= _MAX_FAILS:
        st["open_until"] = time.time() + _RESET_SEC

def _record_success(p: str, m: str) -> None:
    if (p, m) in _CB:
        _CB[(p, m)] = {"fail_count": 0, "open_until": 0}

def _fallbacks(primary: Tuple[str, str]) -> List[Tuple[str, str]]:
    p = primary[0]
    order = {
        "gemini": [("openai", "gpt-4o-mini"), ("anthropic", "claude-3-5-sonnet-20240620")],
        "openai": [("gemini", "gemini-1.5-pro"), ("anthropic", "claude-3-5-sonnet-20240620")],
        "anthropic": [("openai", "gpt-4o-mini"), ("gemini", "gemini-1.5-pro")],
    }
    return order.get(p, [("openai", "gpt-4o-mini"), ("gemini", "gemini-1.5-pro")])

def generate_json(task: str, prompt: str, schema: Dict[str, Any], provider: Optional[str]=None, model: Optional[str]=None) -> Dict[str, Any]:
    """
    Route with circuit breaker and fallbacks. Logs audit on success or failure.
    """
    start = time.time()
    primary = (provider, model) if (provider and model) else choose_for_task(task)
    candidates: List[Tuple[str, str]] = [primary] + _fallbacks(primary)
    last_err: Optional[str] = None
    for p, m in candidates:
        if _circuit_open(p, m):
            continue
        try:
            cli = get_client(p, m)
            out = cli.generate_json(prompt, schema)
            _record_success(p, m)
            ms = int((time.time() - start) * 1000)
            log_event(actor="router", task=task, provider=p, model=m, prompt_sample=prompt[:4000], success=True, latency_ms=ms)
            return out
        except Exception as e:
            _record_fail(p, m)
            last_err = str(e)
            ms = int((time.time() - start) * 1000)
            log_event(actor="router", task=task, provider=p, model=m, prompt_sample=prompt[:4000], success=False, latency_ms=ms, error=last_err)
            continue
    raise RuntimeError(f"all providers failed for task {task}. last_error={last_err}")