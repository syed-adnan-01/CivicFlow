export type AppRole = 'CITIZEN' | 'OFFICER' | 'OFFICE_ADMIN';

export interface UserProfile {
  id: string;
  firebase_uid: string;
  phone_number?: string | null;
  display_name?: string | null;
  role: AppRole;
  active: boolean;
  office_ids?: string[];
  assigned_counter_ids?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface AuthSession {
  firebaseUser: any | null;
  profile: UserProfile | null;
  role: AppRole | null;
  loading: boolean;
  error: string | null;
}

