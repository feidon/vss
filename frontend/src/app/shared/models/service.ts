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
  readonly path: readonly Node[];
  readonly timetable: readonly TimetableEntry[];
}

export interface StopRequest {
  readonly platform_id: string;
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
