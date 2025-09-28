from __future__ import annotations
from typing import Iterable, Dict, Any
import time
import json
from pathlib import Path

class Trainer:
    def __init__(self, out_dir: str):
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    def train(self, data: Iterable[Dict[str, str]], cfg: Dict[str, Any]) -> Dict[str, Any]:
        # Stub trainer: simulates epochs and writes a log
        epochs = int(cfg.get("epochs", 1))
        seen = 0
        for _ in range(epochs):
            for item in data:
                seen += len(item.get("text", "")) // 80
        log = {"epochs": epochs, "seen_samples_est": seen, "finished_at": time.time()}
        (self.out / "train_log.json").write_text(json.dumps(log, indent=2))
        return log