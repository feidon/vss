import { HttpErrorResponse } from '@angular/common/http';

type ErrorFormatter = (
  context: Readonly<Record<string, unknown>>,
  nameMap: ReadonlyMap<string, string>,
) => string | null;

function name(id: unknown, nameMap: ReadonlyMap<string, string>): string | undefined {
  return typeof id === 'string' ? nameMap.get(id) : undefined;
}

function named(key: string, template: (n: string) => string): ErrorFormatter {
  return (ctx, m) => {
    const n = name(ctx[key], m);
    return n ? template(n) : null;
  };
}

const ERROR_FORMATTERS: Readonly<Record<string, ErrorFormatter>> = {
  VEHICLE_NOT_FOUND: named('vehicle_id', (n) => `Vehicle "${n}" not found`),
  STOP_NOT_FOUND: named('stop_id', (n) => `Stop "${n}" not found`),
  SAME_ORIGIN_DESTINATION: named('stop_id', (n) => `Origin and destination cannot both be "${n}"`),
  BLOCK_NOT_FOUND: named('block_id', (n) => `Block "${n}" not found`),
  PLATFORM_NOT_FOUND: named('platform_id', (n) => `Platform "${n}" not found`),
  UNKNOWN_NODE: named('node_id', (n) => `Unknown node "${n}"`),
  ENTRY_NODE_NOT_IN_ROUTE: named('node_id', (n) => `Node "${n}" is not part of the route`),
  NO_ROUTE_BETWEEN_STOPS: (ctx, m) => {
    const from = name(ctx['from_stop_id'], m);
    const to = name(ctx['to_stop_id'], m);
    return from && to ? `No route between ${from} and ${to}` : null;
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
  INTERVAL_BELOW_MINIMUM: (ctx) => {
    const requested = ctx['requested_interval'];
    const minimum = ctx['minimum_interval'];
    return typeof requested === 'number' && typeof minimum === 'number'
      ? `Interval ${requested}s is below the minimum of ${minimum}s due to interlocking constraints.`
      : null;
  },
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
