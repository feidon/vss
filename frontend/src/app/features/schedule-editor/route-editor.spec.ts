import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouteEditorComponent } from './route-editor';
import { GraphResponse, ServiceResponse } from '../../shared/models';

describe('RouteEditorComponent', () => {
  let fixture: ComponentFixture<RouteEditorComponent>;
  let component: RouteEditorComponent;

  const graph: GraphResponse = {
    nodes: [
      { type: 'platform', id: 'p1', name: 'P1A' },
      { type: 'platform', id: 'p2', name: 'P2A' },
      { type: 'block', id: 'b1', name: 'B1', group: 1, traversal_time_seconds: 30 },
    ],
    connections: [],
    stations: [
      { id: 's1', name: 'S1', is_yard: false, platform_ids: ['p1'] },
      { id: 's2', name: 'S2', is_yard: false, platform_ids: ['p2'] },
      { id: 'y', name: 'Y', is_yard: true, platform_ids: [] },
    ],
    vehicles: [{ id: 'v1', name: 'V1' }],
  };

  const service: ServiceResponse = {
    id: 101,
    name: 'S101',
    vehicle_id: 'v1',
    path: [],
    timetable: [],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RouteEditorComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(RouteEditorComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('service', service);
    fixture.componentRef.setInput('graph', graph);
    await fixture.whenStable();
  });

  it('should display service name', () => {
    expect(fixture.nativeElement.textContent).toContain('S101');
  });

  it('should filter out yard stations from dropdown', () => {
    expect(component.nonYardStations().length).toBe(2);
    expect(component.nonYardStations().every((s) => !s.is_yard)).toBe(true);
  });

  it('should add and remove stops', () => {
    component.selectedPlatformId.set('p1');
    component.addStop();
    component.selectedPlatformId.set('p2');
    component.addStop();

    expect(component.stops().length).toBe(2);
    expect(component.stops()[0].platformName).toBe('P1A');

    component.removeStop(0);
    expect(component.stops().length).toBe(1);
    expect(component.stops()[0].platformName).toBe('P2A');
  });

  it('should update dwell time immutably', () => {
    component.selectedPlatformId.set('p1');
    component.addStop();
    const original = component.stops()[0];

    component.updateDwellTime(0, 60);
    expect(component.stops()[0].dwellTime).toBe(60);
    expect(original.dwellTime).toBe(30); // original unchanged
  });

  it('should disable submit with fewer than 2 stops', async () => {
    component.selectedPlatformId.set('p1');
    component.addStop();
    component.startTimeLocal.set('2025-01-01T10:00');
    fixture.detectChanges();
    await fixture.whenStable();

    const buttons = fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;
    const submitBtn = Array.from(buttons).find((b) => b.textContent?.includes('Update Route'))!;
    expect(submitBtn.disabled).toBe(true);
  });

  it('should emit submitted with correct payload', () => {
    component.selectedPlatformId.set('p1');
    component.addStop();
    component.selectedPlatformId.set('p2');
    component.addStop();
    component.startTimeLocal.set('2025-06-15T10:00');

    let emitted: { stops: { platform_id: string; dwell_time: number }[]; start_time: number } | undefined;
    component.submitted.subscribe((e) => (emitted = e));
    component.onSubmit();

    expect(emitted).toBeDefined();
    expect(emitted!.stops).toEqual([
      { platform_id: 'p1', dwell_time: 30 },
      { platform_id: 'p2', dwell_time: 30 },
    ]);
    expect(emitted!.start_time).toBeGreaterThan(0);
  });

  it('should emit back event', () => {
    let backEmitted = false;
    component.back.subscribe(() => (backEmitted = true));

    const backBtn = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    backBtn.click();
    expect(backEmitted).toBe(true);
  });

  it('should display timetable when service has entries', async () => {
    const serviceWithTimetable: ServiceResponse = {
      ...service,
      timetable: [
        { order: 0, node_id: 'p1', arrival: 1700000000, departure: 1700000030 },
        { order: 1, node_id: 'b1', arrival: 1700000030, departure: 1700000060 },
      ],
    };
    fixture.componentRef.setInput('service', serviceWithTimetable);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('Timetable');
    expect(fixture.nativeElement.textContent).toContain('P1A');
    expect(fixture.nativeElement.textContent).toContain('B1');
  });
});
