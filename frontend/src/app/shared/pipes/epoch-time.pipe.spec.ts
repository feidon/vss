import { EpochTimePipe } from './epoch-time.pipe';
import { epochToDisplayTime } from '../utils/time-utils';

describe('EpochTimePipe', () => {
  const pipe = new EpochTimePipe();

  it('should delegate to epochToDisplayTime for a valid epoch', () => {
    const epoch = 1700000000;
    expect(pipe.transform(epoch)).toBe(epochToDisplayTime(epoch));
  });

  it('should return em dash for zero', () => {
    expect(pipe.transform(0)).toBe('\u2014');
  });

  it('should return em dash for NaN-like falsy values', () => {
    expect(pipe.transform(null as unknown as number)).toBe('\u2014');
    expect(pipe.transform(undefined as unknown as number)).toBe('\u2014');
  });

  it('should pad single-digit hours, minutes, seconds', () => {
    const result = pipe.transform(1700000000);
    const parts = result.split(':');
    expect(parts).toHaveLength(3);
    parts.forEach((part) => {
      expect(part).toHaveLength(2);
    });
  });

  it('should handle small positive epoch value', () => {
    const result = pipe.transform(1);
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
  });
});
