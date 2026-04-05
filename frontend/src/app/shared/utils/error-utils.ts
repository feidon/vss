import { HttpErrorResponse } from '@angular/common/http';

export function extractErrorMessage(error: HttpErrorResponse, fallback: string): string {
  if (error.status >= 500) {
    return 'Something went wrong. Please try again later.';
  }

  const detail = error.error?.detail;

  if (typeof detail === 'string') {
    return detail;
  }

  if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
    return detail.message;
  }

  return fallback;
}
