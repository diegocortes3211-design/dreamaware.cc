import json, glob
from pathlib import Path

def recent_failures(limit=20):
    folder = Path("reports/failures")
    files = sorted(folder.glob("*.json"))[-limit:]
    for p in files:
        rec = json.loads(p.read_text())
        yield {
            "ts": rec["ts"],
            "event": rec["event"],
            "short": (rec.get("error") or {}).get("msg",""),
            "trace": (rec.get("error") or {}).get("trace","")[:800]
        }