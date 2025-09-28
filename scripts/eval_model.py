#!/usr/bin/env python3
import argparse
import json
from packages.modeling.data_loader import load_jsonl
from packages.modeling.evaluator import evaluate

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default="data/processed/train.jsonl")
    args = ap.parse_args()
    ds = list(load_jsonl(args.jsonl))
    metrics = evaluate(ds)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()