import { HttpErrorResponse } from '@angular/common/http';

type ErrorFormatter = (
  context: Readonly<Record<string, unknown>>,
  nameMap: ReadonlyMap<string, string>,
) => string | null;

function name(id: unknown, nameMap: ReadonlyMap<string, string>): string | undefined {
  return typeof id === 'string' ? nameMap.get(id) : undefined;
}

const ERROR_FORMATTERS: Readonly<Record<string, ErrorFormatter>> = {
  VEHICLE_NOT_FOUND: (ctx, m) => {
    const n = name(ctx['vehicle_id'], m);
    return n ? `Vehicle "${n}" not found` : null;
  },
  STOP_NOT_FOUND: (ctx, m) => {
    const n = name(ctx['stop_id'], m);
    return n ? `Stop "${n}" not found` : null;
  },
  SAME_ORIGIN_DESTINATION: (ctx, m) => {
    const n = name(ctx['stop_id'], m);
    return n ? `Origin and destination cannot both be "${n}"` : null;
  },
  NO_ROUTE_BETWEEN_STOPS: (ctx, m) => {
    const from = name(ctx['from_stop_id'], m);
    const to = name(ctx['to_stop_id'], m);
    return from && to ? `No route between ${from} and ${to}` : null;
  },
  BLOCK_NOT_FOUND: (ctx, m) => {
    const n = name(ctx['block_id'], m);
    return n ? `Block "${n}" not found` : null;
  },
  PLATFORM_NOT_FOUND: (ctx, m) => {
    const n = name(ctx['platform_id'], m);
    return n ? `Platform "${n}" not found` : null;
  },
  UNKNOWN_NODE: (ctx, m) => {
    const n = name(ctx['node_id'], m);
    return n ? `Unknown node "${n}"` : null;
  },
  ENTRY_NODE_NOT_IN_ROUTE: (ctx, m) => {
    const n = name(ctx['node_id'], m);
    return n ? `Node "${n}" is not part of the route` : null;
  },
  INSUFFICIENT_VEHICLES: (ctx) => {
    const needed = ctx['needed'];
    const available = ctx['available'];
    return typeof needed === 'number' && typeof available === 'number'
      ? `Need ${needed} vehicles but only ${available} available`
      : null;
  },
  SERVICE_NOT_FOUND: (ctx) => {
    const id = ctx['service_id'];
    return typeof id === 'number' ? `Service S${id} not found` : null;
  },
  EMPTY_SERVICE_NAME: () => 'Service name must not be empty',
  INSUFFICIENT_STOPS: () => 'Route must contain at least two stops',
  NOT_A_YARD: () => 'First stop must be a yard',
  DUPLICATE_PLATFORM: () => 'Route contains duplicate platforms',
  EMPTY_ROUTE: () => 'Route must not be empty',
  ROUTE_NOT_CONNECTED: () => 'Route is not connected',
  ARRIVAL_AFTER_DEPARTURE: () => 'Arrival time cannot be after departure time',
  INVALID_TRAVERSAL_TIME: () => 'Invalid traversal time',
  INVALID_INTERVAL: () => 'Invalid schedule interval',
  INVALID_DWELL_TIME: () => 'Invalid dwell time',
  INVALID_TIME_RANGE: () => 'Invalid time range',
};

export function extractErrorMessage(
  error: HttpErrorResponse,
  fallback: string,
  nameMap?: ReadonlyMap<string, string>,
): string {
  if (error.status >= 500) {
    return 'Something went wrong. Please try again later.';
  }

  const detail = error.error?.detail;

  if (typeof detail === 'string') {
    return detail;
  }

  if (detail && typeof detail === 'object' && typeof detail.error_code === 'string') {
    const formatter = ERROR_FORMATTERS[detail.error_code];
    if (formatter) {
      const formatted = formatter(detail.context ?? {}, nameMap ?? new Map());
      if (formatted) return formatted;
    }
  }

  return fallback;
}

export function buildNameMap(
  ...sources: readonly (readonly { readonly id: string; readonly name: string }[])[]
): Map<string, string> {
  const map = new Map<string, string>();
  for (const source of sources) {
    for (const item of source) {
      map.set(item.id, item.name);
    }
  }
  return map;
}
