#!/usr/bin/env python3
"""
packages.visualization.renderers.vega_render

Renders a Vega-Lite JSON specification to an SVG image.

Key functions:
  - render(spec_path: Path, out_path: Path): Renders a single Vega-Lite spec.
"""
import argparse, json, sys
from pathlib import Path


def render(spec_path: Path, out_path: Path) -> None:
    """
    Renders a Vega-Lite JSON spec file to an SVG image using `vl-convert`.

    If the `vl-convert` library is not installed or an error occurs during
    conversion, it prints an error message and skips rendering.

    Args:
        spec_path (Path): The path to the input Vega-Lite JSON file.
        out_path (Path): The path where the output SVG image will be saved.
    """
    try:
        import vl_convert as vlc

        # The vl_spec argument can be either a JSON string or a Python dict
        spec_str = spec_path.read_text(encoding="utf-8")
        svg = vlc.vegalite_to_svg(vl_spec=spec_str)
        out_path.write_text(svg, encoding="utf-8")
        print(f"Rendered {spec_path} -> {out_path}")
    except Exception as e:
        print(f"Skip render for {spec_path} due to missing renderer or error: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    render(args.spec, args.out)

if __name__ == "__main__":
    main()