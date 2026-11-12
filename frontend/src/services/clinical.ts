import { api } from "../api/client";
import type {
  ComparativeStudy,
  Consultation,
  MedicalHistory,
  OdontogramData,
  Paginated,
} from "../types/domain";
import type { ConsentWorkspace, ConsentEvidence } from "../types/compliance";

export const clinicalService = {
  medicalHistory: (patientId: string) =>
    api<MedicalHistory>(`clinics/patients/${patientId}/medical-history/`),
  saveMedicalHistory: (patientId: string, history: MedicalHistory) => {
    const data = { ...history };
    delete data.paciente;
    delete data.paciente_id;
    delete data.medico;
    delete data.medico_id;
    delete data.clinic;
    delete data.clinic_id;
    return api<MedicalHistory>(
      `clinics/patients/${patientId}/medical-history/`,
      { method: "PUT", body: JSON.stringify(data) },
    );
  },
  consultations: (patientId: string, page = 1) =>
    api<Paginated<Consultation>>(
      `clinics/patients/${patientId}/consultations/?page=${page}`,
    ),
  createConsultation: (
    patientId: string,
    values: {
      motivo_consulta: string;
      diagnostico: string;
      tratamiento: string;
      observaciones: string;
    },
  ) =>
    api<Consultation>(`clinics/patients/${patientId}/consultations/`, {
      method: "POST",
      body: JSON.stringify(values),
    }),
  odontogram: (patientId: string) =>
    api<OdontogramData>(`clinics/patients/${patientId}/odontogram/`),
  saveOdontogram: (
    patientId: string,
    values: OdontogramData & { resumen: Record<string, number> },
  ) =>
    api<OdontogramData>(`clinics/patients/${patientId}/odontogram/`, {
      method: "PUT",
      body: JSON.stringify(values),
    }),
  comparativeStudy: (patientId: string) =>
    api<ComparativeStudy>(`clinics/patients/${patientId}/comparative-study/`),
  saveComparativeStudy: (patientId: string, data: FormData) =>
    api<ComparativeStudy>(`clinics/patients/${patientId}/comparative-study/`, {
      method: "PUT",
      body: data,
    }),
  consent: (patientId: string) =>
    api<ConsentWorkspace>(`clinics/patients/${patientId}/consent/`),
  saveConsent: (patientId: string, data: FormData) =>
    api<ConsentEvidence>(`clinics/patients/${patientId}/consent/`, {
      method: "POST",
      body: data,
    }),
};
