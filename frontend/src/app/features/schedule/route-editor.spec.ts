import { TestBed, ComponentFixture } from '@angular/core/testing';
import { RouteEditorComponent } from './route-editor';
import { ServiceDetailResponse, GraphResponse } from '../../shared/models';

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

const mockServiceWithRoute: ServiceDetailResponse = {
  id: 101,
  name: 'S101',
  vehicle_id: 'v1',
  route: [
    { type: 'platform', id: 'p1', name: 'P1A', x: 0, y: 0 },
    { type: 'platform', id: 'p2', name: 'P2A', x: 2, y: 0 },
  ],
  timetable: [
    { order: 0, node_id: 'p1', arrival: 1700000000, departure: 1700000060 },
    { order: 1, node_id: 'p2', arrival: 1700000090, departure: 1700000135 },
  ],
  graph: mockGraph,
};

const mockServiceEmpty: ServiceDetailResponse = {
  id: 102,
  name: 'S102',
  vehicle_id: 'v1',
  route: [],
  timetable: [],
  graph: mockGraph,
};

describe('RouteEditorComponent', () => {
  let fixture: ComponentFixture<RouteEditorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RouteEditorComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(RouteEditorComponent);
  });

  it('should populate stops from existing service route', async () => {
    fixture.componentRef.setInput('service', mockServiceWithRoute);
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();
    await fixture.whenStable();

    const stops = fixture.componentInstance.stops();
    expect(stops.length).toBe(2);
    expect(stops[0].nodeId).toBe('p1');
    expect(stops[0].nodeName).toBe('P1A');
    expect(stops[0].dwellTime).toBe(60);
    expect(stops[1].nodeId).toBe('p2');
    expect(stops[1].nodeName).toBe('P2A');
    expect(stops[1].dwellTime).toBe(45);
  });

  it('should populate start time from existing service timetable', async () => {
    fixture.componentRef.setInput('service', mockServiceWithRoute);
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();
    await fixture.whenStable();

    const startTime = fixture.componentInstance.startTimeLocal();
    expect(startTime).toBeTruthy();
    expect(startTime).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
  });

  it('should leave stops empty for service with no route', async () => {
    fixture.componentRef.setInput('service', mockServiceEmpty);
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.componentInstance.stops().length).toBe(0);
    expect(fixture.componentInstance.startTimeLocal()).toBe('');
  });

  it('should render stop rows in the table', async () => {
    fixture.componentRef.setInput('service', mockServiceWithRoute);
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const tables = fixture.nativeElement.querySelectorAll('table');
    const stopRows = tables[0].querySelectorAll('tbody tr');
    expect(stopRows.length).toBe(2);
    expect(stopRows[0].textContent).toContain('P1A');
    expect(stopRows[1].textContent).toContain('P2A');
  });
});
