import { TestBed } from '@angular/core/testing';
import { TrackMapEditorComponent } from './track-map-editor';
import { GraphResponse } from '../../shared/models';
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
    { id: 's0', name: 'Y', is_yard: true, platform_ids: [] },
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
