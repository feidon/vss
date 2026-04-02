import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ServiceService } from './service.service';
import { ServiceDetailResponse, ServiceResponse } from '../../shared/models';
import { API_BASE_URL } from './api.config';

describe('ServiceService', () => {
  let service: ServiceService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ServiceService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should fetch all services (summary only)', () => {
    const mockServices: ServiceResponse[] = [{ id: 101, name: 'S101', vehicle_id: 'v1' }];

    service.getServices().subscribe((result) => {
      expect(result).toEqual(mockServices);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/services`);
    expect(req.request.method).toBe('GET');
    req.flush(mockServices);
  });

  it('should fetch a single service with detail', () => {
    const mockService: ServiceDetailResponse = {
      id: 101,
      name: 'S101',
      vehicle_id: 'v1',
      route: [{ type: 'platform', id: 'p1', name: 'P1A', x: 0, y: 0 }],
      timetable: [{ order: 0, node_id: 'p1', arrival: 1700000000, departure: 1700000030 }],
      graph: {
        nodes: [],
        connections: [],
        stations: [],
        vehicles: [],
      },
    };

    service.getService(101).subscribe((result) => {
      expect(result).toEqual(mockService);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/services/101`);
    expect(req.request.method).toBe('GET');
    req.flush(mockService);
  });

  it('should create a service', () => {
    service.createService({ name: 'S102', vehicle_id: 'v1' }).subscribe((result) => {
      expect(result).toEqual({ id: 102 });
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/services`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'S102', vehicle_id: 'v1' });
    req.flush({ id: 102 });
  });

  it('should update a route', () => {
    const routeRequest = {
      stops: [{ node_id: 'p1', dwell_time: 30 }],
      start_time: 1700000000,
    };

    service.updateRoute(101, routeRequest).subscribe((result) => {
      expect(result).toEqual({ id: 101 });
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/services/101/route`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(routeRequest);
    req.flush({ id: 101 });
  });

  it('should delete a service', () => {
    service.deleteService(101).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/services/101`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
