export interface BlockResponse {
  readonly id: string;
  readonly name: string;
  readonly group: number;
  readonly traversal_time_seconds: number;
}

export interface UpdateBlockRequest {
  readonly traversal_time_seconds: number;
}

export interface BlockIdResponse {
  readonly id: string;
}
