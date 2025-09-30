import json, os, time, traceback
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

LOG_DIR = os.getenv("FAILURE_LOG_DIR", "reports/failures")
os.makedirs(LOG_DIR, exist_ok=True)

def failure_event(event: str, payload: Dict[str, Any], *, err: Exception | None = None) -> str:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rec = {
        "ts": ts,
        "event": event,
        "payload": payload,
        "error": None if err is None else {
            "type": type(err).__name__,
            "msg": str(err),
            "trace": traceback.format_exc(limit=8)
        }
    }
    path = os.path.join(LOG_DIR, f"{ts}-{event}.json")
    with open(path, "w") as f:
        f.write(json.dumps(rec, ensure_ascii=False, indent=2))
    return path