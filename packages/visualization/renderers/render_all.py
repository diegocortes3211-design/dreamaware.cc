#!/usr/bin/env python3
"""
Render all visualization specs into site assets.
Vega Lite JSON -> SVG via vl-convert if available.
DOT -> SVG via graphviz if available.
"""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[3]
SPECS = ROOT / "packages" / "visualization" / "specs"
OUT = ROOT / "site" / "static" / "assets" / "visuals"
OUT.mkdir(parents=True, exist_ok=True)

def run(cmd):
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