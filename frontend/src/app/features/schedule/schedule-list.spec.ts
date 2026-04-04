import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ScheduleListComponent } from './schedule-list';
import { API_BASE_URL } from '../../core/services/api.config';
import { ServiceDetailResponse, ServiceResponse } from '../../shared/models';

const mockDetail: ServiceDetailResponse = {
  id: 101,
  name: 'S101',
  vehicle_id: 'v1',
  route: [
    { type: 'yard', id: 'y1', name: 'Y', x: 0, y: 0 },
    { type: 'block', id: 'b1', name: 'B1', x: 1, y: 0, group: 0, traversal_time_seconds: 30 },
    { type: 'platform', id: 'p1a', name: 'P1A', x: 2, y: 0 },
  ],
  timetable: [],
  graph: { nodes: [], connections: [], stations: [], vehicles: [] },
};

const mockServices: ServiceResponse[] = [
  {
    id: 101,
    name: 'S101',
    vehicle_id: 'v1',
    vehicle_name: 'V1',
    start_time: 1700000000,
    origin_name: 'P1A',
    destination_name: 'P2A',
  },
  {
    id: 102,
    name: 'S102',
    vehicle_id: 'v2',
    vehicle_name: 'V2',
    start_time: null,
    origin_name: null,
    destination_name: null,
  },
];

describe('ScheduleListComponent', () => {
  let httpTesting: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ScheduleListComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'schedule/:id/edit', component: ScheduleListComponent }]),
      ],
    }).compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should load and display services', async () => {
    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    fixture.detectChanges();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('S101');
    expect(rows[0].textContent).toContain('V1');
    expect(rows[0].textContent).toContain('P1A');
    expect(rows[0].textContent).toContain('P2A');
    expect(rows[1].textContent).toContain('—');
  });

  it('should show empty state when no services exist', async () => {
    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush([]);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No services created yet.');
  });

  it('should delete a service with confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    fixture.detectChanges();

    const deleteBtn = fixture.nativeElement.querySelector('button.bg-red-600');
    deleteBtn.click();
    fixture.detectChanges();

    const deleteReq = httpTesting.expectOne(`${API_BASE_URL}/services/101`);
    expect(deleteReq.request.method).toBe('DELETE');
    deleteReq.flush(null);

    // Reloads list after delete
    httpTesting.expectOne(`${API_BASE_URL}/services`).flush([mockServices[1]]);
    fixture.detectChanges();
  });

  it('should navigate to editor on Edit click', async () => {
    const navigateSpy = vi.spyOn(router, 'navigate');

    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    fixture.detectChanges();

    const editBtns = fixture.nativeElement.querySelectorAll('button.bg-blue-600');
    editBtns[0].click();
    fixture.detectChanges();

    expect(navigateSpy).toHaveBeenCalledWith(['/schedule', 101, 'edit']);
  });

  it('should expand a row on click and fetch detail', () => {
    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    fixture.detectChanges();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    rows[0].click();
    fixture.detectChanges();

    const detailReq = httpTesting.expectOne(`${API_BASE_URL}/services/101`);
    expect(detailReq.request.method).toBe('GET');
    detailReq.flush(mockDetail);
    fixture.detectChanges();

    const expandedRow = fixture.nativeElement.querySelector('tr.bg-gray-50');
    expect(expandedRow).toBeTruthy();
    expect(expandedRow.textContent).toContain('Y → B1 → P1A');
  });

  it('should collapse an expanded row on re-click', () => {
    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    fixture.detectChanges();

    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    rows[0].click();
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockDetail);
    fixture.detectChanges();

    // Click same row again to collapse
    const updatedRows = fixture.nativeElement.querySelectorAll('tbody tr');
    updatedRows[0].click();
    fixture.detectChanges();

    const expandedRow = fixture.nativeElement.querySelector('tr.bg-gray-50');
    expect(expandedRow).toBeNull();
  });

  it('should use cached detail on re-expand without re-fetching', () => {
    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    fixture.detectChanges();

    // Expand
    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    rows[0].click();
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services/101`).flush(mockDetail);
    fixture.detectChanges();

    // Collapse
    fixture.nativeElement.querySelectorAll('tbody tr')[0].click();
    fixture.detectChanges();

    // Re-expand — no new HTTP request
    fixture.nativeElement.querySelectorAll('tbody tr')[0].click();
    fixture.detectChanges();

    httpTesting.expectNone(`${API_BASE_URL}/services/101`);
    const expandedRow = fixture.nativeElement.querySelector('tr.bg-gray-50');
    expect(expandedRow.textContent).toContain('Y → B1 → P1A');
  });

  it('should not toggle expansion when Edit or Delete button is clicked', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');

    const fixture = TestBed.createComponent(ScheduleListComponent);
    fixture.detectChanges();

    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    fixture.detectChanges();

    // Click Edit button
    const editBtn = fixture.nativeElement.querySelector('button.bg-blue-600');
    editBtn.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.expandedServiceId()).toBeNull();
    expect(navigateSpy).toHaveBeenCalled();

    // Click Delete button (cancel the confirm)
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    const deleteBtn = fixture.nativeElement.querySelector('button.bg-red-600');
    deleteBtn.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.expandedServiceId()).toBeNull();
  });
});
