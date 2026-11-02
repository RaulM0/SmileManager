import { api } from "../api/client";
import type { AnalysisResult, ClinicalImage, Paginated } from "../types/domain";

export const imagesService = {
  list: (patientId: string, date: string, consultationId: string, page = 1) => api<Paginated<ClinicalImage>>(`patients/${patientId}/clinical-images/?date=${encodeURIComponent(date)}&consultation_id=${encodeURIComponent(consultationId)}&page=${page}`),
  get: (id: string) => api<ClinicalImage>(`clinical-images/${id}/`),
  upload: (patientId: string, data: FormData) => api<ClinicalImage>(`patients/${patientId}/clinical-images/`, { method: "POST", body: data }),
  remove: (id: number) => api(`clinical-images/${id}/`, { method: "DELETE" }),
  analyze: (id: string, force = false) => api<AnalysisResult>(`clinical-images/${id}/analyze/`, { method: "POST", headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ force }) }),
};
