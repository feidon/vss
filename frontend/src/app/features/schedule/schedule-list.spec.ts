import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ScheduleListComponent } from './schedule-list';
import { API_BASE_URL } from '../../core/services/api.config';
import { ServiceResponse } from '../../shared/models';

const mockServices: ServiceResponse[] = [
  {
    id: 101,
    name: 'S101',
    vehicle_id: 'v1',
    vehicle_name: 'V1',
    start_time: 1700000000,
    origin: 'P1A',
    destination: 'P2A',
  },
  {
    id: 102,
    name: 'S102',
    vehicle_id: 'v2',
    vehicle_name: 'V2',
    start_time: null,
    origin: null,
    destination: null,
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
});
