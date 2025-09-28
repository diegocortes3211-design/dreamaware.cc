from __future__ import annotations
from pathlib import Path
from typing import Iterable, Dict
import json
from .utils.zero_slop import strip_slop

def iter_text_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.suffix.lower() in {".txt", ".md"} and p.is_file():
            yield p

def build_jsonl(raw_dir: str, out_jsonl: str) -> int:
    src = Path(raw_dir)
    dst = Path(out_jsonl)
    dst.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with dst.open("w", encoding="utf-8") as f:
        for fp in iter_text_files(src):
            text = fp.read_text(encoding="utf-8", errors="ignore")
            clean = strip_slop(text)
            if clean:
                item: Dict[str, str] = {"path": str(fp), "text": clean}
                f.write(json.dumps(item) + "\n")
                count += 1
    return count

def load_jsonl(path: str) -> Iterable[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)