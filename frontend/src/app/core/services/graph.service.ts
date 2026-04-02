import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { GraphResponse } from '../../shared/models';
import { API_BASE_URL } from './api.config';

@Injectable({ providedIn: 'root' })
export class GraphService {
  private readonly http = inject(HttpClient);

  getGraph(): Observable<GraphResponse> {
    return this.http.get<GraphResponse>(`${API_BASE_URL}/graph`);
  }
}
