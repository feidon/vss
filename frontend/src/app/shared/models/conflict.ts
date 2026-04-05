export interface VehicleConflict {
  readonly vehicle_id: string;
  readonly service_a_id: number;
  readonly service_b_id: number;
  readonly reason: string;
}

export interface BlockConflict {
  readonly block_id: string;
  readonly service_a_id: number;
  readonly service_b_id: number;
  readonly overlap_start: number;
  readonly overlap_end: number;
}

export interface InterlockingConflict {
  readonly group: number;
  readonly block_a_id: string;
  readonly block_b_id: string;
  readonly service_a_id: number;
  readonly service_b_id: number;
  readonly overlap_start: number;
  readonly overlap_end: number;
}

export interface BatteryConflict {
  readonly type: 'low_battery' | 'insufficient_charge';
  readonly service_id: number;
}

export interface ConflictResponse {
  readonly vehicle_conflicts: readonly VehicleConflict[];
  readonly block_conflicts: readonly BlockConflict[];
  readonly interlocking_conflicts: readonly InterlockingConflict[];
  readonly battery_conflicts: readonly BatteryConflict[];
}
