export interface Office {
  id: string;
  name: string;
  code: string;
  address?: string;
  district?: string;
  state?: string;
  is_active: boolean;
}

export interface ServiceChecklistItem {
  id: string;
  document_name: string;
  is_mandatory: boolean;
  description?: string;
}

export interface Service {
  id: string;
  name: string;
  code: string;
  department: string;
  description: string;
  official_portal_url?: string;
  checklist?: ServiceChecklistItem[];
  is_active: boolean;
}

