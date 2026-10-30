import { ApiErrorResponse } from '../../types/api';

export class ApiError extends Error {
  public code: string;
  public status: number;
  public details?: Record<string, any>;
  public requestId?: string;

  constructor(status: number, errorData?: Partial<ApiErrorResponse>) {
    super(errorData?.message || `API request failed with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = errorData?.code || `HTTP_${status}`;
    this.details = errorData?.details;
    this.requestId = errorData?.request_id;
  }
}

export function getUserFriendlyErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case 'SLOT_FULL':
        return 'This slot was just booked by another citizen. Please pick another available time.';
      case 'SLOT_CLOSED':
        return 'This appointment slot is no longer open for booking.';
      case 'DUPLICATE_BOOKING':
        return 'You already have an active appointment for this service.';
      case 'QR_EXPIRED':
        return 'This QR code has expired. Please use the Rotate QR button on your appointment page to obtain a fresh code.';
      case 'QR_ALREADY_USED':
        return 'This QR code has already been scanned and checked in.';
      case 'ALREADY_CHECKED_IN':
        return 'This citizen appointment is already checked in.';
      case 'INVALID_TOKEN_TRANSITION':
        return 'The queue token state changed. Refreshing queue...';
      case 'COUNTER_BUSY':
        return 'This counter is currently occupied with another token.';
      case 'NOT_ASSIGNED_TO_COUNTER':
        return 'Your account is not assigned to this counter.';
      case 'NO_ELIGIBLE_TOKEN':
        return 'There are no eligible waiting tokens for this counter right now.';
      case 'UNAUTHORIZED':
      case 'HTTP_401':
        return 'Your session has expired. Please sign in again.';
      case 'FORBIDDEN':
      case 'HTTP_403':
        return 'You do not have permission to perform this action.';
      default:
        return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
}

