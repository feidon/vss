import { Component, ElementRef, computed, effect, input, output, viewChild } from '@angular/core';
import * as d3 from 'd3';
import { GraphResponse, Station, Node, Edge, Junction } from '../../shared/models';

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
    <div class="relative overflow-auto bg-panel-base">
      @if (showHint()) {
        <p class="border-b border-edge px-4 py-2 font-display text-xs text-ink-muted">
          Click a platform or yard on the map to add a stop
        </p>
      }
      <svg #mapSvg></svg>
      <div
        #tooltip
        class="pointer-events-none absolute z-10 hidden rounded-md bg-panel-raised px-2.5 py-1.5 font-display text-xs font-medium text-ink shadow-lg ring-1 ring-edge-bright"
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
    svg
      .attr('width', svgWidth)
      .attr('height', svgHeight)
      .attr('class', 'select-none')
      .style('background', '#05080f');

    const queuedSet = new Set(queuedIds);
    const queuedOrder = new Map<string, number>();
    queuedIds.forEach((id, i) => queuedOrder.set(id, i + 1));

    // Define arrowhead marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 10)
      .attr('refY', 5)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 Z')
      .attr('fill', '#4a5c75');

    // Draw station indicator rectangles (behind everything else)
    const stationPadding = 30;
    const minStationSize = 60;
    const nodeMap = new Map(graph.nodes.map((n) => [n.id, n]));

    const stationsWithBounds = graph.stations
      .map((station: Station) => {
        const platforms = station.platform_ids
          .map((pid) => nodeMap.get(pid))
          .filter((n): n is Node => n !== undefined);
        if (platforms.length === 0) return null;

        const sxs = platforms.map((p) => xScale(p.x));
        const sys = platforms.map((p) => yScale(p.y));
        const rawX = Math.min(...sxs) - stationPadding;
        const rawY = Math.min(...sys) - stationPadding;
        const rawW = Math.max(...sxs) - Math.min(...sxs) + stationPadding * 2;
        const rawH = Math.max(...sys) - Math.min(...sys) + stationPadding * 2;
        const cx = rawX + rawW / 2;
        const cy = rawY + rawH / 2;
        const w = Math.max(rawW, minStationSize);
        const h = Math.max(rawH, minStationSize);
        return { station, x: cx - w / 2, y: cy - h / 2, w, h };
      })
      .filter((s): s is NonNullable<typeof s> => s !== null);

    const stationGroups = svg
      .selectAll('g.station')
      .data(stationsWithBounds)
      .enter()
      .append('g')
      .attr('class', 'station')
      .style('pointer-events', 'none');

    stationGroups
      .append('rect')
      .attr('x', (d) => d.x)
      .attr('y', (d) => d.y)
      .attr('width', (d) => d.w)
      .attr('height', (d) => d.h)
      .attr('rx', 8)
      .attr('ry', 8)
      .attr('fill', '#0b1121')
      .attr('stroke', '#1a2744')
      .attr('stroke-width', 1);

    stationGroups
      .append('text')
      .attr('x', (d) => d.x + d.w / 2)
      .attr('y', (d) => d.y + d.h / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-family', 'Rajdhani, sans-serif')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('letter-spacing', '0.05em')
      .attr('fill', '#4a5c75')
      .text((d) => d.station.name);

    // Build node ID set for radius lookup (nodes=12, junctions=4)
    const nodeIdSet = new Set(graph.nodes.map((n) => n.id));
    const targetRadius = (id: string) => (nodeIdSet.has(id) ? 12 : 4);

    // Compute shortened endpoint that stops at target node boundary
    const shortenedEnd = (d: Edge) => {
      const sx1 = xScale(posMap.get(d.from_id)?.x ?? 0);
      const sy1 = yScale(posMap.get(d.from_id)?.y ?? 0);
      const sx2 = xScale(posMap.get(d.to_id)?.x ?? 0);
      const sy2 = yScale(posMap.get(d.to_id)?.y ?? 0);
      const dx = sx2 - sx1;
      const dy = sy2 - sy1;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      const r = targetRadius(d.to_id);
      return { x: sx2 - (dx / len) * r, y: sy2 - (dy / len) * r };
    };

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
      .attr('x2', (d: Edge) => shortenedEnd(d).x)
      .attr('y2', (d: Edge) => shortenedEnd(d).y)
      .attr('stroke', '#263a5c')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)');

    // Block labels offset perpendicular to edge direction (computed in screen space)
    // Group edges by shared endpoint pair for index-based staggering
    const baseOffset = 14;
    const edgePairIndex = new Map<string, number>();
    const edgePairCount = new Map<string, number>();
    for (const edge of graph.edges) {
      const key = [edge.from_id, edge.to_id].sort().join('|');
      const count = edgePairCount.get(key) ?? 0;
      edgePairIndex.set(edge.id, count);
      edgePairCount.set(key, count + 1);
    }

    const edgeLabelPos = (d: Edge) => {
      const sx1 = xScale(posMap.get(d.from_id)?.x ?? 0);
      const sy1 = yScale(posMap.get(d.from_id)?.y ?? 0);
      const sx2 = xScale(posMap.get(d.to_id)?.x ?? 0);
      const sy2 = yScale(posMap.get(d.to_id)?.y ?? 0);
      const dx = sx2 - sx1;
      const dy = sy2 - sy1;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      const idx = edgePairIndex.get(d.id) ?? 0;
      const offset = baseOffset + idx * 14;
      return {
        x: (sx1 + sx2) / 2 + (-dy / len) * offset,
        y: (sy1 + sy2) / 2 + (dx / len) * offset,
      };
    };
    edgeGroups
      .append('text')
      .attr('x', (d: Edge) => edgeLabelPos(d).x)
      .attr('y', (d: Edge) => edgeLabelPos(d).y)
      .attr('text-anchor', 'middle')
      .attr('font-family', 'Azeret Mono, monospace')
      .attr('font-size', '8px')
      .attr('fill', '#3a4d6a')
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
      .attr('fill', '#1a2744')
      .attr('stroke', '#263a5c')
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

    // Glow filter for active nodes
    const defs = svg.select('defs');
    const glowFilter = defs
      .append('filter')
      .attr('id', 'node-glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%');
    glowFilter.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur');
    glowFilter
      .append('feMerge')
      .selectAll('feMergeNode')
      .data(['blur', 'SourceGraphic'])
      .enter()
      .append('feMergeNode')
      .attr('in', (d: string) => d);

    // Node circles
    nodeGroups
      .append('circle')
      .attr('r', 12)
      .attr('fill', (d: Node) =>
        queuedSet.has(d.id) ? '#22c55e' : d.type === 'yard' ? '#eab308' : '#38bdf8',
      )
      .attr('stroke', (d: Node) =>
        queuedSet.has(d.id) ? '#16a34a' : d.type === 'yard' ? '#ca8a04' : '#0ea5e9',
      )
      .attr('stroke-width', 2)
      .attr('filter', (d: Node) => (queuedSet.has(d.id) ? 'url(#node-glow)' : null));

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
      .attr('font-family', 'Rajdhani, sans-serif')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', '#8896ab')
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
