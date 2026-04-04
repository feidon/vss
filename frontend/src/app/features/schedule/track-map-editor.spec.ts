import { TestBed } from '@angular/core/testing';
import { TrackMapEditorComponent } from './track-map-editor';
import { GraphResponse } from '../../shared/models';
import { ComponentFixture } from '@angular/core/testing';

const mockGraph: GraphResponse = {
  nodes: [
    { type: 'platform', id: 'p1', name: 'P1A', x: 0, y: 0 },
    { type: 'block', id: 'b1', name: 'B1', group: 0, traversal_time_seconds: 30, x: 1, y: 0 },
    { type: 'platform', id: 'p2', name: 'P2A', x: 2, y: 0 },
    { type: 'yard', id: 'y1', name: 'Y', x: -1, y: 0 },
  ],
  connections: [
    { from_id: 'y1', to_id: 'p1' },
    { from_id: 'p1', to_id: 'b1' },
    { from_id: 'b1', to_id: 'p2' },
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

  it('should render SVG with nodes', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();

    const svg = fixture.nativeElement.querySelector('svg');
    expect(svg).toBeTruthy();

    // Should have connection lines, block circles, and clickable groups
    const circles = svg.querySelectorAll('circle');
    expect(circles.length).toBeGreaterThan(0);
  });

  it('should emit stopAdded when platform clicked', () => {
    const spy = vi.fn();
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.componentInstance.stopAdded.subscribe(spy);
    fixture.detectChanges();

    const clickableGroups = fixture.nativeElement.querySelectorAll('g.clickable');
    expect(clickableGroups.length).toBe(3); // 2 platforms + 1 yard

    clickableGroups[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(spy).toHaveBeenCalled();
  });

  it('should not be interactive when interactive=false', () => {
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.componentRef.setInput('interactive', false);
    fixture.detectChanges();

    const clickableGroups = fixture.nativeElement.querySelectorAll('g.clickable');
    expect(clickableGroups.length).toBeGreaterThan(0);
    // Non-interactive nodes should have default cursor
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
