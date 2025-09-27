---
id: visualization-guide
title: Visualization Guide
---

This guide maps common tasks to chart types and rendering tools. Specs live in `packages/visualization/specs`. Renderers live in `packages/visualization/renderers`.

## Core tasks
- Deviation: diverging bar, column
- Correlation: scatter, timeline
- Sorting: ranked bar, dot strip
- Distribution: histogram, box plot
- Changes over time: line, calendar heat map
- Magnitude: column, marimekko
- Part of whole: pie, stacked venn
- Spatial: choropleth, flow map

## Advanced
- Alluvial or sankey for flows
- Chord for relationships
- Radial bar for cyclic magnitudes
- Treemap for hierarchical weight
- Pareto for priority ranking
- Taylor and contour for model performance

## Implementation
- Charts: Vega Lite JSON specs rendered to PNG or SVG
- Graphs and flows: DOT or Mermaid rendered to SVG
- All assets land in `site/static/assets/visuals`

## Add a new visual
1. Create a spec in `packages/visualization/specs`
2. Run `python packages/visualization/renderers/render_all.py`
3. Commit the spec and the rendered asset
4. Link it from a doc page