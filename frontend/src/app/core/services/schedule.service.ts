import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { GenerateScheduleRequest, GenerateScheduleResponse } from '../../shared/models';
import { API_BASE_URL } from './api.config';

@Injectable({ providedIn: 'root' })
export class ScheduleService {
  private readonly http = inject(HttpClient);

  generate(request: GenerateScheduleRequest): Observable<GenerateScheduleResponse> {
    return this.http.post<GenerateScheduleResponse>(`${API_BASE_URL}/schedules/generate`, request);
  }
}
