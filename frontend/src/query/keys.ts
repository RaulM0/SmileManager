import { getClinicContext } from "../api/client";

const scope = () => getClinicContext() ?? "unselected";

export const queryKeys = {
  resource: (path: string) => [scope(), "resource", path] as const,
  get patients() { return [scope(), "patients"] as const; },
  patientAutocomplete: (term: string) => [scope(), "patients", "autocomplete", term] as const,
  patientList: (search: string, page: string) => [scope(), "patients", "list", search, page] as const,
  get appointments() { return [scope(), "appointments"] as const; },
  appointmentList: (status: string, search: string) => [scope(), "appointments", "list", status, search] as const,
  get diagnostics() { return [scope(), "diagnostics"] as const; },
  diagnosticList: (filters: string) => [scope(), "diagnostics", "list", filters] as const,
  images: (patientId: string) => [scope(), "images", patientId] as const,
  protectedMedia: (path: string) => [scope(), "protected-media", path] as const,
};
