export interface SessionUser {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_staff: boolean;
  profile: { clinica_nombre: string; telefono: string; direccion: string; extra: string };
}

export interface SessionResponse {
  authenticated: boolean;
  access?: string;
  user?: SessionUser;
}

export interface PatientSummary {
  id: number;
  nombre: string;
  appat: string;
  apmat: string;
  full_name: string;
  estatus: "A" | "I";
}

export interface Patient extends Omit<PatientSummary, "full_name"> {
  full_name?: string;
  fecha_nacimiento: string;
  genero: "M" | "F";
  telefono: string;
  email: string;
  age: number;
  created?: string;
  updated?: string;
}

export interface PatientFormValues {
  nombre: string;
  appat: string;
  apmat: string;
  fecha_nacimiento: string;
  genero: string;
  telefono: string;
  email: string;
  estatus: string;
}

export interface Appointment {
  id: number;
  paciente: PatientSummary;
  fecha: string;
  hora: string;
  motivo: string;
  observaciones: string;
  estatus: "P" | "C" | "A";
  estatus_display?: string;
}

export interface AppointmentFormValues {
  fecha: string;
  hora: string;
  motivo: string;
  observaciones: string;
  estatus: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ClinicalImage {
  id: number;
  paciente: number;
  patient_name: string;
  tipo_imagen: string;
  descripcion: string;
  imagen_url: string;
  resultados_url: string | null;
  fecha_subida: string;
}

export interface Consultation {
  id: number;
  paciente: PatientSummary;
  fecha_consulta: string;
  motivo_consulta: string;
  diagnostico: string;
  tratamiento: string;
  observaciones: string;
}

export interface PatientOption { id: number; text: string }

export interface ComparativeStudy {
  exists: boolean;
  fecha_inicio?: string;
  diagnostico?: string;
  observaciones?: string;
  image_urls?: Record<string, string | null>;
}

export interface Dashboard {
  patient_count: number;
  today_count: number;
  today: Appointment[];
  upcoming: Appointment[];
}

export interface DiagnosticsPageData extends Paginated<ClinicalImage> {
  statistics: { total: number; processed: number; pending: number; processed_percentage: number; type_count: number };
}

export interface Detection {
  clase: string;
  confianza: number;
  coordenadas: number[];
}

export interface AnalysisResult { image: ClinicalImage; detections: Detection[]; run_id?: number; status?: string; disposition?: string }

export interface MedicalHistory extends Record<string, boolean | string | number | null> {
  id: number | null;
}

export interface OdontogramData {
  id?: number | null;
  version?: number;
  denticion_permanente: Record<string, Record<string, string>>;
  denticion_decidua: Record<string, Record<string, string>>;
}

export interface Consent {
  id: number;
  texto: string;
  fecha_aceptacion: string | null;
  archivo_ine_url: string | null;
  pdf_generado: string | null;
}

export type FieldErrors<T extends string = string> = Partial<Record<T | "detail", string | string[]>>;
