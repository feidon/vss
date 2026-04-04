import { Component, ElementRef, computed, effect, input, output, viewChild } from '@angular/core';
import * as d3 from 'd3';
import { GraphResponse, Node, Edge, Junction } from '../../shared/models';

interface Position {
  readonly x: number;
  readonly y: number;
}

export interface MapStopEvent {
  readonly nodeId: string;
  readonly nodeName: string;
}

@Component({
  selector: 'app-track-map-editor',
  template: `
    <div class="relative overflow-auto rounded border bg-gray-50">
      @if (showHint()) {
        <p class="px-3 py-2 text-sm text-gray-500">
          Click a platform or yard on the map to add a stop
        </p>
      }
      <svg #mapSvg></svg>
      <div
        #tooltip
        class="pointer-events-none absolute z-10 hidden rounded bg-gray-900 px-2 py-1 text-xs text-white shadow"
      ></div>
    </div>
  `,
})
export class TrackMapEditorComponent {
  readonly graph = input.required<GraphResponse>();
  readonly queuedNodeIds = input<readonly string[]>([]);
  readonly interactive = input(true);
  readonly stopAdded = output<MapStopEvent>();

  private readonly svgRef = viewChild.required<ElementRef<SVGSVGElement>>('mapSvg');
  private readonly tooltipRef = viewChild.required<ElementRef<HTMLDivElement>>('tooltip');

  readonly showHint = computed(() => this.interactive() && this.queuedNodeIds().length === 0);

  readonly clickableNodes = computed(() =>
    this.graph().nodes.filter((n) => n.type === 'platform' || n.type === 'yard'),
  );

  constructor() {
    effect(() => {
      const graph = this.graph();
      const queued = this.queuedNodeIds();
      if (graph.nodes.length > 0) {
        this.render(graph, queued);
      }
    });
  }

  private render(graph: GraphResponse, queuedIds: readonly string[]): void {
    const svgEl = this.svgRef().nativeElement;
    const tooltipEl = this.tooltipRef().nativeElement;
    const interactive = this.interactive();

    // Build unified position map from nodes + junctions
    const posMap = new Map<string, Position>();
    for (const node of graph.nodes) {
      posMap.set(node.id, node);
    }
    for (const jct of graph.junctions) {
      posMap.set(jct.id, jct);
    }

    const allPositions = [...posMap.values()];
    const margin = 40;
    const xs = allPositions.map((p) => p.x);
    const ys = allPositions.map((p) => p.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const dataWidth = maxX - minX || 1;
    const dataHeight = maxY - minY || 1;
    const svgWidth = 800;
    const svgHeight = Math.max(400, (dataHeight / dataWidth) * svgWidth);

    const xScale = d3
      .scaleLinear()
      .domain([minX, maxX])
      .range([margin, svgWidth - margin]);
    const yScale = d3
      .scaleLinear()
      .domain([minY, maxY])
      .range([margin, svgHeight - margin]);

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('width', svgWidth).attr('height', svgHeight).attr('class', 'select-none');

    const queuedSet = new Set(queuedIds);
    const queuedOrder = new Map<string, number>();
    queuedIds.forEach((id, i) => queuedOrder.set(id, i + 1));

    // Define arrowhead marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 8)
      .attr('refY', 5)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 Z')
      .attr('fill', '#94a3b8');

    // Draw edges (blocks) as labeled lines with direction arrows
    const edgeGroups = svg
      .selectAll('g.edge')
      .data(graph.edges)
      .enter()
      .append('g')
      .attr('class', 'edge');

    edgeGroups
      .append('line')
      .attr('x1', (d: Edge) => xScale(posMap.get(d.from_id)?.x ?? 0))
      .attr('y1', (d: Edge) => yScale(posMap.get(d.from_id)?.y ?? 0))
      .attr('x2', (d: Edge) => xScale(posMap.get(d.to_id)?.x ?? 0))
      .attr('y2', (d: Edge) => yScale(posMap.get(d.to_id)?.y ?? 0))
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)');

    // Block labels offset perpendicular to edge direction (computed in screen space)
    const labelOffset = 10;
    const edgeLabelPos = (d: Edge) => {
      const sx1 = xScale(posMap.get(d.from_id)?.x ?? 0);
      const sy1 = yScale(posMap.get(d.from_id)?.y ?? 0);
      const sx2 = xScale(posMap.get(d.to_id)?.x ?? 0);
      const sy2 = yScale(posMap.get(d.to_id)?.y ?? 0);
      const dx = sx2 - sx1;
      const dy = sy2 - sy1;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      return {
        x: (sx1 + sx2) / 2 + (-dy / len) * labelOffset,
        y: (sy1 + sy2) / 2 + (dx / len) * labelOffset,
      };
    };
    edgeGroups
      .append('text')
      .attr('x', (d: Edge) => edgeLabelPos(d).x)
      .attr('y', (d: Edge) => edgeLabelPos(d).y)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', '#94a3b8')
      .text((d: Edge) => d.name);

    // Draw junction dots (small non-interactive)
    svg
      .selectAll('circle.junction')
      .data(graph.junctions)
      .enter()
      .append('circle')
      .attr('class', 'junction')
      .attr('cx', (d: Junction) => xScale(d.x))
      .attr('cy', (d: Junction) => yScale(d.y))
      .attr('r', 4)
      .attr('fill', '#cbd5e1')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 1);

    // Draw clickable nodes (platforms + yards)
    const nodeGroups = svg
      .selectAll('g.clickable')
      .data(graph.nodes)
      .enter()
      .append('g')
      .attr('class', 'clickable')
      .attr('transform', (d: Node) => `translate(${xScale(d.x)},${yScale(d.y)})`)
      .style('cursor', interactive ? 'pointer' : 'default');

    // Node circles
    nodeGroups
      .append('circle')
      .attr('r', 12)
      .attr('fill', (d: Node) =>
        queuedSet.has(d.id) ? '#2563eb' : d.type === 'yard' ? '#f59e0b' : '#3b82f6',
      )
      .attr('stroke', (d: Node) => (queuedSet.has(d.id) ? '#1d4ed8' : '#1e40af'))
      .attr('stroke-width', 2);

    // Queue order numbers
    nodeGroups
      .filter((d: Node) => queuedOrder.has(d.id))
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .attr('fill', 'white')
      .text((d: Node) => String(queuedOrder.get(d.id) ?? ''));

    // Name labels
    nodeGroups
      .append('text')
      .attr('dy', 22)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#1e293b')
      .text((d: Node) => d.name);

    if (interactive) {
      // Hover feedback
      nodeGroups
        .on('mouseenter', (event: MouseEvent, d: Node) => {
          d3.select(event.currentTarget as SVGGElement)
            .select('circle')
            .attr('stroke-width', 3)
            .attr('r', 14);
          tooltipEl.textContent = d.type === 'yard' ? `${d.name} (Yard)` : d.name;
          tooltipEl.style.left = `${event.offsetX + 16}px`;
          tooltipEl.style.top = `${event.offsetY - 8}px`;
          tooltipEl.classList.remove('hidden');
        })
        .on('mouseleave', (event: MouseEvent) => {
          d3.select(event.currentTarget as SVGGElement)
            .select('circle')
            .attr('stroke-width', 2)
            .attr('r', 12);
          tooltipEl.classList.add('hidden');
        })
        .on('click', (_event: MouseEvent, d: Node) => {
          this.stopAdded.emit({ nodeId: d.id, nodeName: d.name });
        });
    }
  }
}
