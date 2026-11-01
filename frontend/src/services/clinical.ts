import { api } from "../api/client";
import type { ComparativeStudy, Consent, Consultation, MedicalHistory, OdontogramData, Paginated } from "../types/domain";

export const clinicalService = {
  medicalHistory: (patientId: string) => api<MedicalHistory>(`patients/${patientId}/medical-history/`),
  saveMedicalHistory: (patientId: string, history: MedicalHistory) => api<MedicalHistory>(`patients/${patientId}/medical-history/`, { method: "PUT", body: JSON.stringify(history) }),
  consultations: (patientId: string, page = 1) => api<Paginated<Consultation>>(`patients/${patientId}/consultations/?page=${page}`),
  createConsultation: (patientId: string, values: { motivo_consulta: string; diagnostico: string; tratamiento: string; observaciones: string }) => api<Consultation>(`patients/${patientId}/consultations/`, { method: "POST", body: JSON.stringify(values) }),
  odontogram: (patientId: string) => api<OdontogramData>(`patients/${patientId}/odontogram/`),
  saveOdontogram: (patientId: string, values: OdontogramData & { resumen: Record<string, number> }) => api<OdontogramData>(`patients/${patientId}/odontogram/`, { method: "PUT", body: JSON.stringify(values) }),
  comparativeStudy: (patientId: string) => api<ComparativeStudy>(`patients/${patientId}/comparative-study/`),
  saveComparativeStudy: (patientId: string, data: FormData) => api<ComparativeStudy>(`patients/${patientId}/comparative-study/`, { method: "PUT", body: data }),
  consent: (patientId: string) => api<Consent>(`patients/${patientId}/consent/`),
  saveConsent: (patientId: string, data: FormData) => api<Consent>(`patients/${patientId}/consent/`, { method: "POST", body: data }),
};
