import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { GraphService } from './graph.service';
import { GraphResponse } from '../../shared/models';
import { API_BASE_URL } from './api.config';

describe('GraphService', () => {
  let service: GraphService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(GraphService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should fetch graph data', () => {
    const mockResponse: GraphResponse = {
      nodes: [{ type: 'platform', id: 'p1', name: 'P1A', x: 0, y: 0 }],
      connections: [{ from_id: 'p1', to_id: 'b1' }],
      stations: [{ id: 's1', name: 'S1', is_yard: false, platform_ids: ['p1'] }],
      vehicles: [{ id: 'v1', name: 'V1' }],
    };

    service.getGraph().subscribe((result) => {
      expect(result).toEqual(mockResponse);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/graph`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });
});
