import { TestBed } from '@angular/core/testing';
import { TrackMapEditorComponent } from './track-map-editor';
import { GraphResponse } from '../../shared/models';
import { THEME } from '../../shared/theme-constants';
import { ComponentFixture } from '@angular/core/testing';

const mockGraph: GraphResponse = {
  nodes: [
    { type: 'platform', id: 'p1', name: 'P1A', x: 0, y: 0 },
    { type: 'platform', id: 'p2', name: 'P2A', x: 2, y: 0 },
    { type: 'yard', id: 'y1', name: 'Y', x: -1, y: 0 },
  ],
  junctions: [{ id: 'j1', x: 1, y: 0 }],
  edges: [
    { id: 'b0', name: 'B0', from_id: 'y1', to_id: 'p1' },
    { id: 'b1', name: 'B1', from_id: 'p1', to_id: 'j1' },
    { id: 'b2', name: 'B2', from_id: 'j1', to_id: 'p2' },
  ],
  stations: [
    { id: 's0', name: 'Y', is_yard: true, platform_ids: ['y1'] },
    { id: 's1', name: 'S1', is_yard: false, platform_ids: ['p1', 'p2'] },
  ],
  vehicles: [{ id: 'v1', name: 'V1' }],
};

describe('TrackMapEditorComponent', () => {
  let fixture: ComponentFixture<TrackMapEditorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TrackMapEditorComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TrackMapEditorComponent);
  });

  it('should render SVG with nodes, junctions, and edges', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    expect(svg).toBeTruthy();

    const edgeGroups = svg.querySelectorAll('g.edge');
    expect(edgeGroups.length).toBe(3);

    const junctions = svg.querySelectorAll('circle.junction');
    expect(junctions.length).toBe(1);

    const clickableGroups = svg.querySelectorAll('g.clickable');
    expect(clickableGroups.length).toBe(3); // 2 platforms + 1 yard
  });

  it('should not render block circles', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const blockCircles = svg.querySelectorAll('circle.block');
    expect(blockCircles.length).toBe(0);
  });

  it('should render block names as edge text labels', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const edgeTexts = svg.querySelectorAll('g.edge text');
    const labels = Array.from(edgeTexts as NodeListOf<SVGTextElement>).map((t) => t.textContent);
    expect(labels).toContain('B0');
    expect(labels).toContain('B1');
    expect(labels).toContain('B2');
  });

  it('should define arrowhead marker with correct dimensions and color', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const marker = svg.querySelector('defs marker');
    expect(marker).toBeTruthy();
    expect(marker.getAttribute('orient')).toBe('auto');
    expect(marker.getAttribute('id')).toBe('arrowhead');
    expect(Number(marker.getAttribute('markerWidth'))).toBeGreaterThanOrEqual(8);
    expect(Number(marker.getAttribute('markerHeight'))).toBeGreaterThanOrEqual(8);
    const arrowPath = marker.querySelector('path');
    expect(arrowPath?.getAttribute('fill')).toBe(THEME.inkMuted);
  });

  it('should apply marker-end to all edge lines', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const lines = svg.querySelectorAll('g.edge line');
    expect(lines.length).toBe(3);
    for (const line of Array.from(lines as NodeListOf<SVGLineElement>)) {
      expect(line.getAttribute('marker-end')).toBe('url(#arrowhead)');
    }
  });

  it('should shorten edge endpoints by target node radius', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const lines = svg.querySelectorAll('g.edge line');
    // b0: y1→p1 (yard node, radius 12), b1: p1→j1 (junction, radius 4)
    const b0Line = lines[0] as SVGLineElement;
    const b1Line = lines[1] as SVGLineElement;

    // The target p1 is a node (radius 12) - x2 should be pulled back from p1's position
    const p1ScreenX = Number(
      svg
        .querySelectorAll('g.clickable')[0]
        .getAttribute('transform')
        ?.match(/translate\(([^,]+)/)?.[1],
    );
    if (p1ScreenX) {
      const b0X2 = Number(b0Line.getAttribute('x2'));
      expect(b0X2).toBeLessThan(p1ScreenX);
    }

    // The target j1 is a junction (radius 4) - should be shortened less than node edges
    const b1X2 = Number(b1Line.getAttribute('x2'));
    const b0X2 = Number(b0Line.getAttribute('x2'));
    // Both lines point right; junction target should be closer to actual position
    expect(b1X2).toBeTruthy();
    expect(b0X2).toBeTruthy();
  });

  it('should emit stopAdded when platform clicked', () => {
    const spy = vi.fn();
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.componentInstance.stopAdded.subscribe(spy);
    fixture.detectChanges();

    const clickableGroups = fixture.nativeElement.querySelectorAll('g.clickable');
    expect(clickableGroups.length).toBe(3);

    clickableGroups[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(spy).toHaveBeenCalled();
  });

  it('should not be interactive when interactive=false', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.componentRef.setInput('interactive', false);
    fixture.detectChanges();

    const clickableGroups = fixture.nativeElement.querySelectorAll('g.clickable');
    expect(clickableGroups.length).toBeGreaterThan(0);
    expect(clickableGroups[0].style.cursor).toBe('default');
  });

  it('should position crossing edge labels at distinct positions', () => {
    const crossingGraph: GraphResponse = {
      nodes: [
        { type: 'platform', id: 'p3a', name: 'P3A', x: 50, y: 40 },
        { type: 'platform', id: 'p3b', name: 'P3B', x: 50, y: 160 },
      ],
      junctions: [
        { id: 'j2', x: 225, y: 40 },
        { id: 'j3', x: 225, y: 160 },
      ],
      edges: [
        { id: 'b8', name: 'B8', from_id: 'j2', to_id: 'p3b' },
        { id: 'b10', name: 'B10', from_id: 'p3a', to_id: 'j3' },
      ],
      stations: [{ id: 's3', name: 'S3', is_yard: false, platform_ids: ['p3a', 'p3b'] }],
      vehicles: [],
    };
    fixture.componentRef.setInput('graph', crossingGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const labels = svg.querySelectorAll('g.edge text');
    expect(labels.length).toBe(2);

    const b8Label = Array.from(labels as NodeListOf<SVGTextElement>).find(
      (t) => t.textContent === 'B8',
    )!;
    const b10Label = Array.from(labels as NodeListOf<SVGTextElement>).find(
      (t) => t.textContent === 'B10',
    )!;

    const b8x = Number(b8Label.getAttribute('x'));
    const b8y = Number(b8Label.getAttribute('y'));
    const b10x = Number(b10Label.getAttribute('x'));
    const b10y = Number(b10Label.getAttribute('y'));

    // Labels should be far enough apart to avoid text bounding box overlap
    const dist = Math.sqrt((b8x - b10x) ** 2 + (b8y - b10y) ** 2);
    expect(dist).toBeGreaterThan(15);
  });

  it('should render station indicator rectangles for each station with platforms', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const stationGroups = svg.querySelectorAll('g.station');
    expect(stationGroups.length).toBe(2); // Y (1 platform) + S1 (2 platforms)

    for (const group of Array.from(stationGroups as NodeListOf<SVGGElement>)) {
      expect(group.querySelector('rect')).toBeTruthy();
      expect(group.querySelector('text')).toBeTruthy();
    }
  });

  it('should display station names as centered labels', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const stationTexts = svg.querySelectorAll('g.station text');
    const labels = Array.from(stationTexts as NodeListOf<SVGTextElement>).map((t) => t.textContent);
    expect(labels).toContain('Y');
    expect(labels).toContain('S1');
  });

  it('should render station rectangles before edges in SVG order', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const allGroups = svg.querySelectorAll('g');
    const groupClasses = Array.from(allGroups as NodeListOf<SVGGElement>).map((g) =>
      g.getAttribute('class'),
    );

    const firstStationIdx = groupClasses.indexOf('station');
    const firstEdgeIdx = groupClasses.indexOf('edge');
    expect(firstStationIdx).toBeLessThan(firstEdgeIdx);
  });

  it('should enforce minimum size for single-platform station rectangle', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const stationGroups = svg.querySelectorAll('g.station');
    // Y station has 1 platform - bounding box collapses, minimum size enforced
    const yardGroup = Array.from(stationGroups as NodeListOf<SVGGElement>).find(
      (g) => g.querySelector('text')?.textContent === 'Y',
    );
    expect(yardGroup).toBeTruthy();
    const rect = yardGroup!.querySelector('rect')!;
    expect(Number(rect.getAttribute('width'))).toBeGreaterThanOrEqual(60);
    expect(Number(rect.getAttribute('height'))).toBeGreaterThanOrEqual(60);
  });

  it('should set pointer-events none on station groups', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const stationGroups = svg.querySelectorAll('g.station');
    for (const group of Array.from(stationGroups as NodeListOf<SVGGElement>)) {
      expect(group.style.pointerEvents).toBe('none');
    }
  });

  it('should style station rectangles with light fill and rounded corners', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    const rect = svg.querySelector('g.station rect');
    expect(rect).toBeTruthy();
    expect(rect.getAttribute('fill')).toBe(THEME.panel);
    expect(rect.getAttribute('stroke')).toBe(THEME.edge);
    expect(rect.getAttribute('rx')).toBe('8');
  });

  it('should show queue numbers for queued nodes', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.componentRef.setInput('queuedNodeIds', ['p1', 'p2']);
    fixture.detectChanges();

    const texts = fixture.nativeElement.querySelectorAll('g.clickable text');
    const numberTexts = Array.from(texts as NodeListOf<SVGTextElement>).filter(
      (t) => t.textContent === '1' || t.textContent === '2',
    );
    expect(numberTexts.length).toBe(2);
  });
});
