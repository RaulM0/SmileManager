import { api } from "../api/client";
import type { Appointment, AppointmentFormValues, Paginated } from "../types/domain";

export const appointmentsService = {
  list: (status: string, search: string, page = 1) => api<Paginated<Appointment>>(`appointments/?status=${status}&search=${encodeURIComponent(search)}&page=${page}`),
  range: async (status: string, search: string, from: string, to: string) => {
    const result: Appointment[] = [];
    let page = 1;
    while (true) {
      const params = new URLSearchParams({ status, search, from, to, page: String(page), page_size: '100' });
      const response = await api<Paginated<Appointment>>(`appointments/?${params}`);
      result.push(...response.results);
      if (!response.next) return result;
      page += 1;
    }
  },
  get: (id: string) => api<Appointment>(`appointments/${id}/`),
  create: (patientId: number, form: AppointmentFormValues) => api<Appointment>("appointments/", { method: "POST", body: JSON.stringify({ ...form, paciente_id: patientId }) }),
  update: (id: string, patientId: number, form: AppointmentFormValues) => api<Appointment>(`appointments/${id}/`, { method: "PATCH", body: JSON.stringify({ ...form, paciente_id: patientId }) }),
  transition: (id: number, name: "complete" | "cancel") => api<Appointment>(`appointments/${id}/${name}/`, { method: "POST" }),
};
