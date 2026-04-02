import { EpochTimePipe } from './epoch-time.pipe';

describe('EpochTimePipe', () => {
  const pipe = new EpochTimePipe();

  it('should format a valid epoch timestamp as HH:mm:ss', () => {
    // 1700000000 = 2023-11-14T22:13:20Z
    const result = pipe.transform(1700000000);
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
  });

  it('should return em dash for zero', () => {
    expect(pipe.transform(0)).toBe('\u2014');
  });

  it('should return em dash for NaN-like falsy values', () => {
    expect(pipe.transform(null as unknown as number)).toBe('\u2014');
    expect(pipe.transform(undefined as unknown as number)).toBe('\u2014');
  });

  it('should pad single-digit hours, minutes, seconds', () => {
    // 1700000000 in local time — verify padding format
    const result = pipe.transform(1700000000);
    const parts = result.split(':');
    expect(parts).toHaveLength(3);
    parts.forEach((part) => {
      expect(part).toHaveLength(2);
    });
  });

  it('should handle midnight epoch (small positive value)', () => {
    // epoch 0 is falsy, but epoch 1 should produce a time string
    const result = pipe.transform(1);
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
  });
});
