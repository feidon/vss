import { GraphResponse } from './graph';
import { Node } from './node';

export interface TimetableEntry {
  readonly order: number;
  readonly node_id: string;
  readonly arrival: number;
  readonly departure: number;
}

export interface ServiceResponse {
  readonly id: number;
  readonly name: string;
  readonly vehicle_id: string;
  readonly vehicle_name: string;
  readonly start_time: number | null;
  readonly origin_name: string | null;
  readonly destination_name: string | null;
}

export interface ServiceDetailResponse {
  readonly id: number;
  readonly name: string;
  readonly vehicle_id: string;
  readonly route: readonly Node[];
  readonly timetable: readonly TimetableEntry[];
  readonly graph: GraphResponse;
}

export interface StopRequest {
  readonly node_id: string;
  readonly dwell_time: number;
}

export interface UpdateRouteRequest {
  readonly stops: readonly StopRequest[];
  readonly start_time: number;
}

export interface CreateServiceRequest {
  readonly name: string;
  readonly vehicle_id: string;
}

export interface ServiceIdResponse {
  readonly id: number;
}
