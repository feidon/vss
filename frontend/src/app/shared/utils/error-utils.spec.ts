import { HttpErrorResponse } from '@angular/common/http';
import { buildNameMap, extractErrorMessage } from './error-utils';

describe('extractErrorMessage', () => {
  const fallback = 'Something failed.';

  it('should return generic message for 500+ status', () => {
    const err = new HttpErrorResponse({ status: 500 });
    expect(extractErrorMessage(err, fallback)).toBe(
      'Something went wrong. Please try again later.',
    );
  });

  it('should return generic message for 502 status', () => {
    const err = new HttpErrorResponse({ status: 502 });
    expect(extractErrorMessage(err, fallback)).toBe(
      'Something went wrong. Please try again later.',
    );
  });

  it('should return string detail when present', () => {
    const err = new HttpErrorResponse({
      status: 400,
      error: { detail: 'Invalid input' },
    });
    expect(extractErrorMessage(err, fallback)).toBe('Invalid input');
  });

  it('should return fallback when no detail present', () => {
    const err = new HttpErrorResponse({ status: 400, error: {} });
    expect(extractErrorMessage(err, fallback)).toBe(fallback);
  });

  it('should return fallback when error body is null', () => {
    const err = new HttpErrorResponse({ status: 404, error: null });
    expect(extractErrorMessage(err, fallback)).toBe(fallback);
  });

  it('should return fallback when detail is a non-message object', () => {
    const err = new HttpErrorResponse({
      status: 422,
      error: { detail: { code: 'INVALID' } },
    });
    expect(extractErrorMessage(err, fallback)).toBe(fallback);
  });

  describe('error code formatting with name map', () => {
    it('should format NO_ROUTE_BETWEEN_STOPS with resolved names', () => {
      const err = new HttpErrorResponse({
        status: 422,
        error: {
          detail: {
            error_code: 'NO_ROUTE_BETWEEN_STOPS',
            context: { from_stop_id: 'uuid-1', to_stop_id: 'uuid-2' },
          },
        },
      });
      const nameMap = new Map([
        ['uuid-1', 'P1A'],
        ['uuid-2', 'P2B'],
      ]);
      expect(extractErrorMessage(err, fallback, nameMap)).toBe('No route between P1A and P2B');
    });

    it('should format STOP_NOT_FOUND with resolved name', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'STOP_NOT_FOUND',
            context: { stop_id: 'abc-123' },
          },
        },
      });
      const nameMap = new Map([['abc-123', 'P1A']]);
      expect(extractErrorMessage(err, fallback, nameMap)).toBe('Stop "P1A" not found');
    });

    it('should format VEHICLE_NOT_FOUND with resolved name', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'VEHICLE_NOT_FOUND',
            context: { vehicle_id: 'v1-uuid' },
          },
        },
      });
      const nameMap = new Map([['v1-uuid', 'V1']]);
      expect(extractErrorMessage(err, fallback, nameMap)).toBe('Vehicle "V1" not found');
    });

    it('should format BLOCK_NOT_FOUND with resolved name', () => {
      const err = new HttpErrorResponse({
        status: 404,
        error: {
          detail: {
            error_code: 'BLOCK_NOT_FOUND',
            context: { block_id: 'b3-uuid' },
          },
        },
      });
      const nameMap = new Map([['b3-uuid', 'B3']]);
      expect(extractErrorMessage(err, fallback, nameMap)).toBe('Block "B3" not found');
    });

    it('should format INSUFFICIENT_VEHICLES with counts', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'INSUFFICIENT_VEHICLES',
            context: { needed: 3, available: 2 },
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe('Need 3 vehicles but only 2 available');
    });

    it('should format SERVICE_NOT_FOUND with service id', () => {
      const err = new HttpErrorResponse({
        status: 404,
        error: {
          detail: {
            error_code: 'SERVICE_NOT_FOUND',
            context: { service_id: 101 },
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe('Service S101 not found');
    });

    it('should format simple error codes without context', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'EMPTY_SERVICE_NAME',
            context: {},
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe('Service name must not be empty');
    });

    it('should format INSUFFICIENT_STOPS', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'INSUFFICIENT_STOPS',
            context: {},
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe('Route must contain at least two stops');
    });

    it('should return fallback when UUID not in name map', () => {
      const err = new HttpErrorResponse({
        status: 422,
        error: {
          detail: {
            error_code: 'NO_ROUTE_BETWEEN_STOPS',
            context: { from_stop_id: 'uuid-1', to_stop_id: 'uuid-2' },
          },
        },
      });
      const nameMap = new Map<string, string>();
      expect(extractErrorMessage(err, fallback, nameMap)).toBe(fallback);
    });

    it('should format INTERVAL_BELOW_MINIMUM with interval values', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'INTERVAL_BELOW_MINIMUM',
            context: {
              requested_interval: 59,
              minimum_interval: 60,
              dwell_time: 15,
              min_departure_gap: 75,
            },
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe(
        'Interval 59s is below the minimum of 60s due to interlocking constraints.',
      );
    });

    it('should return fallback for INTERVAL_BELOW_MINIMUM with missing context', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'INTERVAL_BELOW_MINIMUM',
            context: {},
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe(fallback);
    });

    it('should return fallback for unknown error code', () => {
      const err = new HttpErrorResponse({
        status: 400,
        error: {
          detail: {
            error_code: 'SOME_FUTURE_ERROR',
            context: {},
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe(fallback);
    });

    it('should still return generic message for 500 even with error_code', () => {
      const err = new HttpErrorResponse({
        status: 500,
        error: {
          detail: {
            error_code: 'INTERNAL',
            context: {},
          },
        },
      });
      expect(extractErrorMessage(err, fallback)).toBe(
        'Something went wrong. Please try again later.',
      );
    });
  });
});

describe('buildNameMap', () => {
  it('should build map from single source', () => {
    const nodes = [
      { id: 'a', name: 'P1A' },
      { id: 'b', name: 'B3' },
    ];
    const map = buildNameMap(nodes);
    expect(map.get('a')).toBe('P1A');
    expect(map.get('b')).toBe('B3');
    expect(map.size).toBe(2);
  });

  it('should merge multiple sources', () => {
    const nodes = [{ id: 'a', name: 'P1A' }];
    const vehicles = [{ id: 'v1', name: 'V1' }];
    const map = buildNameMap(nodes, vehicles);
    expect(map.get('a')).toBe('P1A');
    expect(map.get('v1')).toBe('V1');
    expect(map.size).toBe(2);
  });

  it('should return empty map for no sources', () => {
    const map = buildNameMap();
    expect(map.size).toBe(0);
  });

  it('should handle later source overriding earlier', () => {
    const a = [{ id: 'x', name: 'First' }];
    const b = [{ id: 'x', name: 'Second' }];
    const map = buildNameMap(a, b);
    expect(map.get('x')).toBe('Second');
  });
});
