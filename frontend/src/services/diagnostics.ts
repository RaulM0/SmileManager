import { api } from "../api/client";
import type { DiagnosticsPageData } from "../types/domain";

export const diagnosticsService = {
  list: (filters: string) =>
    api<DiagnosticsPageData>(`clinics/diagnostics/?${filters}`),
};
