export type AppointmentStatus =
  | 'BOOKED'
  | 'CHECKED_IN'
  | 'RESCHEDULED'
  | 'CANCELLED'
  | 'NO_SHOW';

export interface AppointmentSlot {
  slot_id: string;
  start_time: string; // ISO 8601
  end_time: string;   // ISO 8601
  total_capacity: number;
  available_capacity: number;
  is_available: boolean;
}

export interface Appointment {
  id: string;
  appointment_reference: string;
  citizen_id: string;
  office_id: string;
  service_id: string;
  slot_start: string;
  slot_end: string;
  status: AppointmentStatus;
  qr_reference?: string; // Returned on create or rotate
  qr_expires_at?: string;
  created_at: string;
  office_name?: string;
  service_name?: string;
}

export interface CreateAppointmentRequest {
  service_id: string;
  office_id: string;
  slot_start: string;
  slot_end: string;
  notes?: string;
}

export interface QrRotationResponse {
  appointment_id: string;
  qr_reference: string;
  qr_expires_at: string;
  rotated_at: string;
}

