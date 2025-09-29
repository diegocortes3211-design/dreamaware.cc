#!/usr/bin/env python3
"""
packages.visualization.renderers.graphviz_render

Renders a Graphviz DOT file to an SVG image.

Key functions:
  - render(dot_path: Path, out_path: Path): Renders a single DOT file.
"""
import argparse
from pathlib import Path


def render(dot_path: Path, out_path: Path) -> None:
    """
    Renders a Graphviz DOT file to an SVG image using the `graphviz` library.

    If the `graphviz` library is not installed or if any other error occurs,
    it prints an error message and skips rendering.

    Args:
        dot_path (Path): The path to the input DOT file.
        out_path (Path): The path where the output SVG image will be saved.
    """
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