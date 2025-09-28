#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from packages.modeling.data_loader import build_jsonl, load_jsonl
from packages.modeling.model import get_model
from packages.modeling.tokenizer import get_tokenizer
from packages.modeling.trainer import Trainer
from packages.modeling.evaluator import evaluate

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--jsonl", default="data/processed/train.jsonl")
    ap.add_argument("--artifacts", default="artifacts/model")
    ap.add_argument("--model-name", default="")
    ap.add_argument("--epochs", type=int, default=1)
    args = ap.parse_args()

    Path(args.artifacts).mkdir(parents=True, exist_ok=True)
    n = build_jsonl(args.raw, args.jsonl)
    ds = list(load_jsonl(args.jsonl))
    cfg = {"model_name": args.model_name, "epochs": args.epochs}
    _tok = get_tokenizer(args.model_name)
    _mdl = get_model(cfg)

    trainer = Trainer(args.artifacts)
    train_log = trainer.train(ds, cfg)
    metrics = evaluate(ds)
    report = {"train": train_log, "metrics": metrics}
    (Path(args.artifacts) / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()