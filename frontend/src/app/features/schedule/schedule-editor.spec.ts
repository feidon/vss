import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ScheduleEditorComponent } from './schedule-editor';
import { API_BASE_URL } from '../../core/services/api.config';
import { ServiceDetailResponse } from '../../shared/models';

const mockServiceDetail: ServiceDetailResponse = {
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
  graph: {
    nodes: [
      { type: 'platform', id: 'p1', name: 'P1A', x: 0, y: 0 },
      { type: 'platform', id: 'p2', name: 'P2A', x: 2, y: 0 },
    ],
    junctions: [{ id: 'j1', x: 1, y: 0 }],
    edges: [
      { id: 'b1', name: 'B1', from_id: 'p1', to_id: 'j1' },
      { id: 'b2', name: 'B2', from_id: 'j1', to_id: 'p2' },
    ],
    stations: [{ id: 's1', name: 'S1', is_yard: false, platform_ids: ['p1', 'p2'] }],
    vehicles: [{ id: 'v1', name: 'V1' }],
  },
};

describe('ScheduleEditorComponent', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ScheduleEditorComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => '101' } } },
        },
      ],
    }).compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should load service detail on init', async () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.textContent).toContain('S101');
  });

  it('should show Back to Schedule link', async () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
    fixture.detectChanges();

    const link = fixture.nativeElement.querySelector('a[routerLink="/schedule"]');
    expect(link).toBeTruthy();
    expect(link.textContent).toContain('Back to Schedule');
  });

  it('should show loading state before service loads', () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Loading service...');

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
  });

  it('should set errorMessage on 500 route update', async () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
    fixture.detectChanges();
    await fixture.whenStable();

    const component = fixture.componentInstance;
    component.onRouteSubmitted({
      stops: [
        { node_id: 'p1', dwell_time: 60 },
        { node_id: 'p2', dwell_time: 45 },
      ],
      start_time: 1700000000,
    });

    httpTesting
      .expectOne(`${API_BASE_URL}/services/101/route`)
      .flush('Internal Server Error', { status: 500, statusText: 'Internal Server Error' });

    expect(component.errorMessage()).toBe('Something went wrong. Please try again later.');
    expect(component.conflicts()).toBeNull();
  });

  it('should set errorMessage on network error', async () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
    fixture.detectChanges();
    await fixture.whenStable();

    const component = fixture.componentInstance;
    component.onRouteSubmitted({
      stops: [
        { node_id: 'p1', dwell_time: 60 },
        { node_id: 'p2', dwell_time: 45 },
      ],
      start_time: 1700000000,
    });

    httpTesting
      .expectOne(`${API_BASE_URL}/services/101/route`)
      .error(new ProgressEvent('error'), { status: 0, statusText: 'Unknown Error' });

    expect(component.errorMessage()).toBe('Failed to update route. Please try again.');
    expect(component.conflicts()).toBeNull();
  });

  it('should clear errorMessage on new submission', async () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
    fixture.detectChanges();
    await fixture.whenStable();

    const component = fixture.componentInstance;
    component.errorMessage.set('previous error');

    component.onRouteSubmitted({
      stops: [{ node_id: 'p1', dwell_time: 60 }],
      start_time: 1700000000,
    });

    expect(component.errorMessage()).toBeNull();
    expect(component.conflicts()).toBeNull();

    httpTesting.expectOne(`${API_BASE_URL}/services/101/route`).flush({});
    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
  });

  it('should resolve UUIDs to names in structured error message', async () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
    fixture.detectChanges();
    await fixture.whenStable();

    const component = fixture.componentInstance;
    component.onRouteSubmitted({
      stops: [
        { node_id: 'p1', dwell_time: 60 },
        { node_id: 'p2', dwell_time: 45 },
      ],
      start_time: 1700000000,
    });

    httpTesting.expectOne(`${API_BASE_URL}/services/101/route`).flush(
      {
        detail: {
          error_code: 'NO_ROUTE_BETWEEN_STOPS',
          context: { from_stop_id: 'p1', to_stop_id: 'p2' },
        },
      },
      { status: 422, statusText: 'Unprocessable Entity' },
    );

    expect(component.errorMessage()).toBe('No route between P1A and P2A');
    expect(component.conflicts()).toBeNull();
  });

  it('should set conflicts signal on 409 route update', async () => {
    const fixture = TestBed.createComponent(ScheduleEditorComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockServiceDetail);
    fixture.detectChanges();
    await fixture.whenStable();

    const component = fixture.componentInstance;
    component.onRouteSubmitted({
      stops: [
        { node_id: 'p1', dwell_time: 60 },
        { node_id: 'p2', dwell_time: 45 },
      ],
      start_time: 1700000000,
    });

    const conflictBody = {
      detail: {
        message: 'Conflicts detected',
        vehicle_conflicts: [
          {
            vehicle_id: 'v1',
            service_a_id: 101,
            service_b_id: 102,
            reason: 'Overlapping time windows',
          },
        ],
        block_conflicts: [],
        interlocking_conflicts: [],
        battery_conflicts: [],
      },
    };

    httpTesting
      .expectOne(`${API_BASE_URL}/services/101/route`)
      .flush(conflictBody, { status: 409, statusText: 'Conflict' });

    fixture.detectChanges();
    await fixture.whenStable();

    expect(component.conflicts()).toBeTruthy();
    expect(component.conflicts()!.vehicle_conflicts.length).toBe(1);
  });
});
