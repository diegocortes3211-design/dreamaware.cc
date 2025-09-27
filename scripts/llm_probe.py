#!/usr/bin/env python3
import argparse, json, time
from services.llm.router import generate

def main():
    ap = argparse.ArgumentParser(description="Probe a single provider and model")
    ap.add_argument("--provider", required=True, help="openai|anthropic|gemini|grok")
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--max-tokens", type=int, default=600)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args()
    res = generate(args.provider, args.model, args.prompt, max_tokens=args.max_tokens, temperature=args.temperature)
    print(json.dumps({
        "provider": res.provider,
        "model": res.model,
        "latency_ms": res.latency_ms,
        "input_tokens": res.input_tokens,
        "output_tokens": res.output_tokens,
        "cost_usd": res.cost_usd,
        "text": res.text,
    }, indent=2))

if __name__ == "__main__":
    main()