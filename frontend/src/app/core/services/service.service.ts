import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ServiceResponse,
  ServiceIdResponse,
  CreateServiceRequest,
  UpdateRouteRequest,
} from '../../shared/models';
import { API_BASE_URL } from './api.config';

@Injectable({ providedIn: 'root' })
export class ServiceService {
  private readonly http = inject(HttpClient);

  getServices(): Observable<ServiceResponse[]> {
    return this.http.get<ServiceResponse[]>(`${API_BASE_URL}/services`);
  }

  getService(id: number): Observable<ServiceResponse> {
    return this.http.get<ServiceResponse>(`${API_BASE_URL}/services/${id}`);
  }

  createService(request: CreateServiceRequest): Observable<ServiceIdResponse> {
    return this.http.post<ServiceIdResponse>(`${API_BASE_URL}/services`, request);
  }

  updateRoute(id: number, request: UpdateRouteRequest): Observable<ServiceIdResponse> {
    return this.http.patch<ServiceIdResponse>(`${API_BASE_URL}/services/${id}/route`, request);
  }

  deleteService(id: number): Observable<void> {
    return this.http.delete<void>(`${API_BASE_URL}/services/${id}`);
  }
}
