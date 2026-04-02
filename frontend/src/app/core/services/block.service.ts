import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BlockResponse, BlockIdResponse, UpdateBlockRequest } from '../../shared/models';
import { API_BASE_URL } from './api.config';

@Injectable({ providedIn: 'root' })
export class BlockService {
  private readonly http = inject(HttpClient);

  getBlocks(): Observable<BlockResponse[]> {
    return this.http.get<BlockResponse[]>(`${API_BASE_URL}/blocks`);
  }

  updateBlock(id: string, request: UpdateBlockRequest): Observable<BlockIdResponse> {
    return this.http.patch<BlockIdResponse>(`${API_BASE_URL}/blocks/${id}`, request);
  }
}
