#!/usr/bin/env python3
import argparse, json, os, time
from pathlib import Path
from services.llm.router import generate

def main():
    ap = argparse.ArgumentParser(description="Run the same prompt across multiple providers")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--providers", default="openai:gpt-4o-mini,anthropic:claude-3-5-haiku,gemini:gemini-2.0-flash")
    ap.add_argument("--outdir", default="logs/multimodel")
    args = ap.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    results = []
    for item in [x.strip() for x in args.providers.split(",") if x.strip()]:
        prov, model = [p.strip() for p in item.split(":", 1)]
        try:
            r = generate(prov, model, args.prompt, max_tokens=600, temperature=0.2)
            results.append({
                "provider": r.provider, "model": r.model, "latency_ms": r.latency_ms,
                "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
                "cost_usd": r.cost_usd, "text": r.text
            })
        except Exception as e:
            results.append({"provider": prov, "model": model, "error": str(e)})

    stamp = int(time.time())
    path = outdir / f"bench_{stamp}.json"
    path.write_text(json.dumps({"prompt": args.prompt, "results": results}, indent=2), encoding="utf-8")
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()