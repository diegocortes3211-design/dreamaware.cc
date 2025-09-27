#!/usr/bin/env python3
"""
Generate coverage badge from coverage.xml -> assets/badges/coverage.svg
Color thresholds:
 red < 60
 yellow < 80
 green >= 80
"""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(".")
xml_path = root / "coverage.xml"
if not xml_path.exists():
    raise SystemExit("coverage.xml not found")

tree = ET.parse(xml_path)
cov = tree.getroot()

# coverage.py writes line-rate at root; fall back to totals if needed
rate = cov.attrib.get("line-rate")
percent = 0
if rate is not None:
    percent = round(float(rate) * 100)
else:
    totals = cov.find("totals")
    if totals is not None and "lines-covered" in totals.attrib and "lines-valid" in totals.attrib:
        covered = int(totals.attrib["lines-covered"])
        valid = int(totals.attrib["lines-valid"]) or 1
        percent = round(covered * 100 / valid)

if percent < 60:
    color = "#e5534b"
elif percent < 80:
    color = "#ffcc00"
else:
    color = "#2ea44f"

label = "coverage"
value = f"{percent}%"

# simple width calc
left_w = 80
right_w = max(60, 8 * len(value))
total_w = left_w + right_w

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{label}: {value}">
 <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
 <rect rx="3" width="{total_w}" height="20" fill="#555"/>
 <rect rx="3" x="{left_w}" width="{right_w}" height="20" fill="{color}"/>
 <path fill="{color}" d="M{left_w} 0h4v20h-4z"/>
 <rect rx="3" width="{total_w}" height="20" fill="url(#s)"/>
 <g fill="#fff" text-anchor="start" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
 <text x="6" y="14">{label}</text>
 <text x="{left_w + 8}" y="14">{value}</text>
 </g>
</svg>
"""
out_dir = root / "assets" / "badges"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "coverage.svg").write_text(svg, encoding="utf-8")
print("Wrote", out_dir / "coverage.svg")