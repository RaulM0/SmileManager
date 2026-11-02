export const queryKeys = {
  resource: (path: string) => ["resource", path] as const,
  patients: ["patients"] as const,
  patientAutocomplete: (term: string) => ["patients", "autocomplete", term] as const,
  patientList: (search: string, page: string) => ["patients", "list", search, page] as const,
  appointments: ["appointments"] as const,
  appointmentList: (status: string, search: string) => ["appointments", "list", status, search] as const,
  diagnostics: ["diagnostics"] as const,
  diagnosticList: (filters: string) => ["diagnostics", "list", filters] as const,
  images: (patientId: string) => ["images", patientId] as const,
};
