import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ScheduleViewerComponent } from './schedule-viewer';
import { ServiceResponse, GraphResponse } from '../../shared/models';
import { API_BASE_URL } from '../../core/services/api.config';

describe('ScheduleViewerComponent', () => {
  let fixture: ComponentFixture<ScheduleViewerComponent>;
  let httpTesting: HttpTestingController;

  const mockGraph: GraphResponse = {
    nodes: [{ type: 'platform', id: 'p1', name: 'P1A' }],
    connections: [],
    stations: [{ id: 's1', name: 'S1', is_yard: false, platform_ids: ['p1'] }],
    vehicles: [{ id: 'v1', name: 'V1' }],
  };

  const mockServices: ServiceResponse[] = [
    {
      id: 101,
      name: 'S101',
      vehicle_id: 'v1',
      path: [{ type: 'platform', id: 'p1', name: 'P1A' }],
      timetable: [{ order: 0, node_id: 'p1', arrival: 1700000000, departure: 1700000030 }],
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ScheduleViewerComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpTesting = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ScheduleViewerComponent);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  function flushInitialRequests(): void {
    httpTesting.expectOne(`${API_BASE_URL}/services`).flush(mockServices);
    httpTesting.expectOne(`${API_BASE_URL}/graph`).flush(mockGraph);
    fixture.detectChanges();
  }

  it('should load services and graph on init', async () => {
    fixture.detectChanges(); // triggers ngOnInit
    flushInitialRequests();
    await fixture.whenStable();

    expect(fixture.componentInstance.services()).toEqual(mockServices);
    expect(fixture.componentInstance.vehicles()).toEqual(mockGraph.vehicles);
  });

  it('should show service list by default', async () => {
    fixture.detectChanges();
    flushInitialRequests();
    await fixture.whenStable();

    expect(fixture.nativeElement.querySelector('app-viewer-service-list')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-timetable-detail')).toBeNull();
  });

  it('should show timetable detail when service selected', async () => {
    fixture.detectChanges();
    flushInitialRequests();
    await fixture.whenStable();

    fixture.componentInstance.onSelectService(mockServices[0]);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.querySelector('app-timetable-detail')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-viewer-service-list')).toBeNull();
  });

  it('should return to list when back is triggered', async () => {
    fixture.detectChanges();
    flushInitialRequests();
    await fixture.whenStable();

    fixture.componentInstance.onSelectService(mockServices[0]);
    fixture.detectChanges();

    fixture.componentInstance.onBackToList();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.nativeElement.querySelector('app-viewer-service-list')).toBeTruthy();
    expect(fixture.componentInstance.selectedService()).toBeNull();
  });

  it('should resolve vehicle name for selected service', async () => {
    fixture.detectChanges();
    flushInitialRequests();
    await fixture.whenStable();

    fixture.componentInstance.onSelectService(mockServices[0]);
    expect(fixture.componentInstance.selectedVehicleName()).toBe('V1');
  });
});
