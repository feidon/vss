import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { VehicleService } from './vehicle.service';
import { Vehicle } from '../../shared/models';
import { API_BASE_URL } from './api.config';

describe('VehicleService', () => {
  let service: VehicleService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(VehicleService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should fetch all vehicles', () => {
    const mockVehicles: Vehicle[] = [
      { id: 'v1', name: 'V1' },
      { id: 'v2', name: 'V2' },
      { id: 'v3', name: 'V3' },
    ];

    service.getVehicles().subscribe((result) => {
      expect(result).toEqual(mockVehicles);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/vehicles`);
    expect(req.request.method).toBe('GET');
    req.flush(mockVehicles);
  });
});
