import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BlockService } from './block.service';
import { BlockResponse } from '../../shared/models';
import { API_BASE_URL } from './api.config';

describe('BlockService', () => {
  let service: BlockService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(BlockService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should fetch all blocks', () => {
    const mockBlocks: BlockResponse[] = [
      { id: 'b1', name: 'B1', group: 1, traversal_time_seconds: 30 },
      { id: 'b2', name: 'B2', group: 1, traversal_time_seconds: 45 },
    ];

    service.getBlocks().subscribe((result) => {
      expect(result).toEqual(mockBlocks);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/blocks`);
    expect(req.request.method).toBe('GET');
    req.flush(mockBlocks);
  });

  it('should update block traversal time', () => {
    const blockId = 'b1';

    service.updateBlock(blockId, { traversal_time_seconds: 60 }).subscribe((result) => {
      expect(result).toEqual({ id: blockId });
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/blocks/${blockId}`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ traversal_time_seconds: 60 });
    req.flush({ id: blockId });
  });
});
