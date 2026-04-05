export interface ErrorDetail {
  readonly error_code: string;
  readonly context: Readonly<Record<string, unknown>>;
}
