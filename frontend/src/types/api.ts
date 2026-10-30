export interface ApiErrorResponse {
  code: string;
  message: string;
  request_id?: string;
  details?: Record<string, any>;
}

export interface ApiResponse<T> {
  data: T;
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
  };
}

