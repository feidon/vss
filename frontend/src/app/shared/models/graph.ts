import { Node } from './node';

export interface Edge {
  readonly id: string;
  readonly name: string;
  readonly from_id: string;
  readonly to_id: string;
}

export interface Junction {
  readonly id: string;
  readonly x: number;
  readonly y: number;
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
  readonly junctions: readonly Junction[];
  readonly edges: readonly Edge[];
  readonly stations: readonly Station[];
  readonly vehicles: readonly Vehicle[];
}
