#!/usr/bin/env python3
"""
packages.visualization.renderers.render_all

This script serves as an orchestration layer to render all visualization
specifications into static site assets. It discovers spec files (Vega-Lite JSON,
Graphviz DOT) and delegates rendering to specialized scripts.

This script is intended to be run directly.
"""
from pathlib import Path
import subprocess, sys
from typing import List

ROOT = Path(__file__).resolve().parents[3]
SPECS = ROOT / "packages" / "visualization" / "specs"
OUT = ROOT / "site" / "static" / "assets" / "visuals"
OUT.mkdir(parents=True, exist_ok=True)


def run(cmd: List[str]):
    """
    Executes a command in a subprocess and prints an error if it fails.

    Args:
        cmd (List[str]): The command to execute as a list of strings.
    """
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Renderer error:", e)


for p in SPECS.glob("*.vl.json"):
    out = OUT / (p.stem + ".svg")
    run([sys.executable, str(Path(__file__).parent / "vega_render.py"), str(p), "--out", str(out)])

for p in SPECS.glob("*.dot"):
    out = OUT / (p.stem + ".svg")
    run([sys.executable, str(Path(__file__).parent / "graphviz_render.py"), str(p), "--out", str(out)])

print("Render pipeline finished.")