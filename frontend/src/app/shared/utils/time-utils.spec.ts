import { localDatetimeToEpoch, epochToLocalDatetime, epochToDisplayTime } from './time-utils';

describe('TimeUtils', () => {
  describe('localDatetimeToEpoch', () => {
    it('should convert a datetime-local string to epoch seconds', () => {
      const epoch = localDatetimeToEpoch('2024-01-15T08:00');
      expect(typeof epoch).toBe('number');
      expect(epoch).toBeGreaterThan(0);
    });
  });

  describe('epochToLocalDatetime', () => {
    it('should return a datetime-local formatted string', () => {
      const result = epochToLocalDatetime(1705305600);
      expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
    });

    it('should pad single-digit values', () => {
      const result = epochToLocalDatetime(1705305600);
      const [datePart, timePart] = result.split('T');
      const [, month, day] = datePart.split('-');
      const [hour, minute] = timePart.split(':');
      expect(month).toHaveLength(2);
      expect(day).toHaveLength(2);
      expect(hour).toHaveLength(2);
      expect(minute).toHaveLength(2);
    });
  });

  describe('epochToDisplayTime', () => {
    it('should return HH:MM:SS formatted string', () => {
      const result = epochToDisplayTime(1705305600);
      expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
    });

    it('should return em dash for zero', () => {
      expect(epochToDisplayTime(0)).toBe('\u2014');
    });

    it('should return em dash for null', () => {
      expect(epochToDisplayTime(null as unknown as number)).toBe('\u2014');
    });

    it('should pad single-digit time components', () => {
      const result = epochToDisplayTime(1705305600);
      const parts = result.split(':');
      expect(parts).toHaveLength(3);
      parts.forEach((part) => {
        expect(part).toHaveLength(2);
      });
    });
  });

  describe('round-trip', () => {
    it('should round-trip localDatetimeToEpoch and epochToLocalDatetime', () => {
      const original = '2024-06-15T14:30';
      const epoch = localDatetimeToEpoch(original);
      const roundTripped = epochToLocalDatetime(epoch);
      expect(roundTripped).toBe(original);
    });

    it('should round-trip for midnight', () => {
      const original = '2024-01-01T00:00';
      const epoch = localDatetimeToEpoch(original);
      const roundTripped = epochToLocalDatetime(epoch);
      expect(roundTripped).toBe(original);
    });

    it('should round-trip for end of day', () => {
      const original = '2024-12-31T23:59';
      const epoch = localDatetimeToEpoch(original);
      const roundTripped = epochToLocalDatetime(epoch);
      expect(roundTripped).toBe(original);
    });
  });
});
