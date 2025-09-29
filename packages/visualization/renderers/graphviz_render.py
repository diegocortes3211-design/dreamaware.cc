#!/usr/bin/env python3
import argparse
from pathlib import Path

def render(dot_path: Path, out_path: Path) -> None:
    try:
        from graphviz import Source
        src = Source(dot_path.read_text(encoding="utf-8"))
        src.format = "svg"
        svg = src.pipe().decode("utf-8")
        out_path.write_text(svg, encoding="utf-8")
        print(f"Rendered {dot_path} -> {out_path}")
    except Exception as e:
        print(f"Skip render for {dot_path} due to missing renderer or error: {e}")

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    render(args.spec, args.out)

if __name__ == "__main__":
    main()