export type User = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  last_login: string | null;
  backoffice_assigned?: boolean;
  administrative_account?: boolean;
  patient_count?: number;
};
export type Event = {
  id: number;
  timestamp: string;
  actor_username: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  outcome: string;
  request_id: string;
};
export type Run = {
  id: number;
  status: string;
  requested_at: string;
  started_at: string;
  completed_at: string | null;
  requested_by_id: number | null;
  model_name: string;
  model_version: string;
  failure_category: string;
  request_id: string;
  potentially_stale: boolean;
};
export type Dashboard = {
  users: { active: number; inactive: number };
  ai: { running: number; failed: number; stale: number } | null;
  ai_enabled: boolean;
  patients_active?: number;
  appointments?: { today: number; upcoming: number };
  recent_admin_events: Event[];
};
export type System = { application: string; database: string; ai: string };
