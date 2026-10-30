export type QueueTokenStatus =
  | 'WAITING'
  | 'CALLED'
  | 'SERVING'
  | 'ON_HOLD'
  | 'COMPLETED'
  | 'NO_SHOW'
  | 'CANCELLED';

export type QueueTokenSource = 'APPOINTMENT' | 'WALK_IN' | 'OFFLINE_REGISTER';

export interface QueueToken {
  id: string;
  token_number: string;
  office_id: string;
  service_id: string;
  appointment_id?: string | null;
  counter_id?: string | null;
  status: QueueTokenStatus;
  source: QueueTokenSource;
  estimated_wait_minutes?: number | null;
  tokens_ahead?: number | null;
  called_at?: string | null;
  served_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  counter_name?: string | null;
  service_name?: string | null;
}

export interface Counter {
  id: string;
  office_id: string;
  name: string;
  counter_number: number;
  is_active: boolean;
  assigned_officer_id?: string | null;
  current_token?: QueueToken | null;
}

export interface QueueSnapshot {
  office_id: string;
  waiting_count: number;
  serving_count: number;
  tokens: QueueToken[];
  last_updated: string;
}

export interface CheckinResult {
  token_id: string;
  token_number: string;
  appointment_id: string;
  office_id: string;
  status: QueueTokenStatus;
  created_at: string;
}

