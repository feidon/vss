import { Node } from './node';

export interface Connection {
  readonly from_id: string;
  readonly to_id: string;
}

export interface Station {
  readonly id: string;
  readonly name: string;
  readonly is_yard: boolean;
  readonly platform_ids: readonly string[];
}

export interface Vehicle {
  readonly id: string;
  readonly name: string;
}

export interface GraphResponse {
  readonly nodes: readonly Node[];
  readonly connections: readonly Connection[];
  readonly stations: readonly Station[];
  readonly vehicles: readonly Vehicle[];
}
