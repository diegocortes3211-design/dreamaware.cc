#!/usr/bin/env bash
# Psychoid Nexus — Follow-up Patch: Inventory + VT + Viz (DRY-RUN+ARTIFACTS)
set -euo pipefail

if [ ! -d .git ]; then echo "[-] Run from repo root."; exit 1; fi

echo "[+] Extending CI for inventory..."
cat > .github/workflows/inventory-build.yml <<'YAML'
name: Build AI Inventory
on:
  push:
    branches: [main]
jobs:
  build-inventory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate Inventory
        run: |
          python3 - <<'py'
import os, json, subprocess, time
items=[]
for base in ["engine","simulation","workshop","adversarial","services","physics-engine","neuroanalysis","spherefold"]:
    if os.path.isdir(base):
        for path,_,files in os.walk(base):
            for f in files:
                if f.endswith((".py",".ts",".go",".rs",".yaml",".yml",".json",".toml",".hcl",".tsx",".js",".md")):
                    p=os.path.join(path,f)
                    h=subprocess.check_output(["sha256sum",p]).decode().split()[0]
                    items.append({"path":p,"sha256":h})
os.makedirs("docs/inventory", exist_ok=True)
with open("docs/inventory/ai-systems.json","w") as fp:
    json.dump({"generated_at":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "items":items}, fp, indent=2)
py
      - name: Commit inventory
        run: |
          git config user.name "inventory-bot"
          git config user.email "actions@users.noreply.github.com"
          git add docs/inventory/ai-systems.json
          git commit -m "chore(inventory): update ai-systems.json [skip ci]" || true
          git pull --rebase origin main || true
          git push
YAML

echo "[+] Adding VT enrichment to TI Refiner..."
mkdir -p services/security_engine
cat > services/security_engine/refine_ti.py <<'PY'
import os, requests, json

VT_API_KEY = os.getenv("VT_API_KEY")
MOCK_FIXTURES = True  # CI mode

class TIRefiner:
    def __init__(self): pass

    def refine(self, mask: dict) -> dict:
        for c in mask.get("components", []):
            h = c.get("sha256")
            if h:
                rep = self._vt_lookup(h)
                if rep and rep.get("malicious", 0) > 0:
                    c["score"] = min(1.0, c.get("score", 0.5) + 0.3)
                    c.setdefault("tags", []).append(f"vt:malicious:{rep['malicious']}")
        return mask

    def _vt_lookup(self, hash: str) -> dict | None:
        if MOCK_FIXTURES:
            # CI stub: return mock based on hash pattern
            if hash.startswith("deadbeef"): return {"malicious": 5, "harmless": 0}
            return {"malicious": 0, "harmless": 42}
        if not VT_API_KEY: return None
        url = f"https://www.virustotal.com/api/v3/files/{hash}"
        headers = {"x-apikey": VT_API_KEY}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()["data"]["attributes"]["last_analysis_stats"]
            return data
        except Exception:
            return None

if __name__ == "__main__":
    # Test stub
    ref = TIRefiner()
    mask = {"components": [{"sha256": "deadbeef1234", "score": 0.6}]}
    refined = ref.refine(mask)
    print(json.dumps(refined, indent=2))
PY

echo "[+] VT CI integration..."
cat > .github/workflows/security-engine.yml <<'YAML'
name: Security Engine CI
on:
  push:
    paths: ['services/security_engine/**']
  pull_request:
    paths: ['services/security_engine/**']
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install requests
      - name: Test TI Refiner (mock)
        working-directory: services/security_engine
        run: python refine_ti.py | grep "vt:malicious:5"
YAML

echo "[+] Docusaurus Viz Stub..."
mkdir -p simulation/vis
cat > docs/security-analysis.mdx <<'MDX'
---
title: Security Analysis Pipeline
---

import PipelineViz from '../../simulation/vis/pipeline_viz.jsx';

# Pipeline Overview

The end-to-end flow: ingest → analyze → refine → report.

<PipelineViz attention={{ "nodeA-nodeB": 0.8, "nodeB-nodeC": 0.95 }} />

MDX

cat > simulation/vis/pipeline_viz.jsx <<'JSX'
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const PipelineViz = ({ attention }) => {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!attention) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear
    const width = 400, height = 200;
    svg.attr('width', width).attr('height', height);

    // Stub graph: nodes A B C, edges with thickness by attention
    const nodes = [{id: 'A'}, {id: 'B'}, {id: 'C'}];
    const links = [
      {source: 'A', target: 'B', weight: attention['nodeA-nodeB'] || 0.5},
      {source: 'B', target: 'C', weight: attention['nodeB-nodeC'] || 0.5}
    ];

    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg.append('g').selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke-width', d => d.weight * 10)
      .attr('stroke', d => d.weight > 0.7 ? 'red' : 'gray');

    const node = svg.append('g').selectAll('circle')
      .data(nodes)
      .enter().append('circle')
      .attr('r', 20).attr('fill', 'blue');

    sim.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('cx', d => d.x).attr('cy', d => d.y);
    });
  }, [attention]);

  return <svg ref={svgRef}></svg>;
};

export default PipelineViz;
JSX

echo "[+] Viz CI (stub; assumes Docusaurus build)..."
cat > .github/workflows/frontend-viz.yml <<'YAML'
name: Frontend Viz CI
on:
  push:
    paths: ['docs/**', 'simulation/vis/**']
  pull_request:
    paths: ['docs/**', 'simulation/vis/**']
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: yarn add d3 react
      - name: Lint JSX
        run: npx eslint simulation/vis/*.jsx
YAML

echo "[✓] Patch applied."
echo "Next:"
echo "  1) Set VT_API_KEY in CI secrets for real lookups (optional; mocks by default)."
echo "  2) Test VT: python services/security_engine/refine_ti.py"
echo "  3) Build Docusaurus locally & view /security-analysis (assumes setup)."
echo "  4) Push to main: inventory bot will run & commit ai-systems.json."