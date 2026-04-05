import { HttpErrorResponse } from '@angular/common/http';
import { extractErrorMessage } from './error-utils';

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

  it('should return detail.message when detail is an object', () => {
    const err = new HttpErrorResponse({
      status: 409,
      error: { detail: { message: 'Conflicts detected' } },
    });
    expect(extractErrorMessage(err, fallback)).toBe('Conflicts detected');
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
});
