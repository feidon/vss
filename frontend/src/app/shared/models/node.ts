export interface BlockNode {
  readonly type: 'block';
  readonly id: string;
  readonly name: string;
  readonly group: number;
  readonly traversal_time_seconds: number;
}

export interface PlatformNode {
  readonly type: 'platform';
  readonly id: string;
  readonly name: string;
}

export interface YardNode {
  readonly type: 'yard';
  readonly id: string;
  readonly name: string;
}

export type Node = BlockNode | PlatformNode | YardNode;
