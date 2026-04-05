export interface GenerateScheduleRequest {
  readonly interval_seconds: number;
  readonly start_time: number;
  readonly end_time: number;
  readonly dwell_time_seconds: number;
}

export interface GenerateScheduleResponse {
  readonly services_created: number;
  readonly vehicles_used: readonly string[];
  readonly cycle_time_seconds: number;
}
