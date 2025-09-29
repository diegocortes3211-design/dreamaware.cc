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
