#!/usr/bin/env python3
"""
CLI for Agentics planning and self-modification.
"""
import argparse
import json
from pathlib import Path
from .executive import plan
from .self_modify import propose

def _format_plan(items: list[dict]) -> str:
    lines = []
    for i, it in enumerate(items, 1):
        name = it.get("name", "")
        just = it.get("justification", "")
        inputs = it.get("inputs", {})
        lines.append(f'{i}. {name} inputs={json.dumps(inputs)} reason={just}')
    return "\n".join(lines) or "(empty plan)"

def _format_proposals(items: list[dict]) -> str:
    lines = []
    for i, it in enumerate(items, 1):
        tgt = it.get("target", "")
        ctype = it.get("change_type", "")
        rat = it.get("rationale", "")
        steps = it.get("steps", [])
        lines.append(f'{i}. {tgt} [{ctype}] reason={rat} steps={json.dumps(steps)}')
    return "\n".join(lines) or "(no proposals)"

def main():
    parser = argparse.ArgumentParser(description="Agentics CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pplan = sub.add_parser("plan", help="Generate an execution plan")
    pplan.add_argument("objective", help="High-level objective string")
    pplan.add_argument(
        "--catalog",
        default="services/agentics/catalog/actions.yaml",
        help="Path to action catalog YAML"
    )
    pplan.add_argument("--pretty", action="store_true", help="Pretty print instead of raw JSON")
    pplan.add_argument("--out", help="Write JSON to this path")

    pprop = sub.add_parser("propose", help="Generate improvement proposals")
    pprop.add_argument("--eval-json", required=True, help="Path to JSON file with evaluation results")
    pprop.add_argument("--pretty", action="store_true", help="Pretty print instead of raw JSON")
    pprop.add_argument("--out", help="Write JSON to this path")

    args = parser.parse_args()

    if args.cmd == "plan":
        data = {"plan": plan(args.objective, args.catalog)}
        if args.out:
            Path(args.out).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(_format_plan(data["plan"]) if args.pretty else json.dumps(data, indent=2))
    elif args.cmd == "propose":
        with open(args.eval_json, encoding="utf-8") as f:
            eval_data = json.load(f)
        data = {"proposals": propose(eval_data)}
        if args.out:
            Path(args.out).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(_format_proposals(data["proposals"]) if args.pretty else json.dumps(data, indent=2))

if __name__ == "__main__":
    main()