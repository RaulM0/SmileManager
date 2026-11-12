import { api } from "../api/client";
import type {
  Paginated,
  Patient,
  PatientFormValues,
  PatientOption,
} from "../types/domain";

export const patientsService = {
  list: (search: string, page: string) =>
    api<Paginated<Patient>>(
      `clinics/patients/?search=${encodeURIComponent(search)}&page=${page}`,
    ),
  get: (id: string) => api<Patient>(`clinics/patients/${id}/`),
  create: (values: PatientFormValues) =>
    api<Patient>("clinics/patients/", {
      method: "POST",
      body: JSON.stringify(values),
    }),
  update: (id: string, values: PatientFormValues) =>
    api<Patient>(`clinics/patients/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(values),
    }),
  deactivate: (id: string) =>
    api<Patient>(`clinics/patients/${id}/deactivate/`, { method: "POST" }),
  autocomplete: (term: string) =>
    api<{ results: PatientOption[] }>(
      `clinics/patients/autocomplete/?term=${encodeURIComponent(term)}`,
    ),
  email: (id: number, values: { asunto: string; mensaje: string }) =>
    api<{ detail: string }>(`clinics/patients/${id}/email/`, {
      method: "POST",
      body: JSON.stringify(values),
    }),
};
