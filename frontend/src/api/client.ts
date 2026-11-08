import type { FieldErrors } from "../types/domain";

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;
// Only coalesce simultaneous, ordinary JSON reads. Never retain clinical data here.
const pendingReads = new Map<string, Promise<unknown>>();
let clinicId: string | null = null;
let clinicGeneration = 0;
const inFlightRequests = new Set<AbortController>();

// The header selects a requested context; the server authorizes it on every request.
export function setClinicContext(id: string | null) {
  if (id === clinicId) return;
  clinicId = id;
  clinicGeneration += 1;
  pendingReads.clear();
  for (const controller of inFlightRequests) controller.abort();
  inFlightRequests.clear();
}

export function getClinicContext() { return clinicId; }

// Clinical screens still use the legacy URL vocabulary. Route them to the
// equivalent clinic API only when a clinic is selected. Missing operations
// fail closed in the clinic API instead of falling back to legacy access.
function clinicPath(path: string): string {
  if (!clinicId) return path;
  if (/^clinical-images\/\d+\/file\/(?:\?|$)/.test(path))
    return `clinics/${path.replace('/file/', '/original/file/')}`;
  if (/^clinical-images\/\d+\/result-file\/(?:\?|$)/.test(path))
    return `clinics/${path.replace('/result-file/', '/result/file/')}`;
  if (/^patients\/\d+\/consent\/file\/(?:\?|$)/.test(path))
    return `clinics/${path.replace('/consent/file/', '/consent/identity/file/')}`;
  if (/^(dashboard|patients|appointments|consultations|clinical-images|diagnostics|exports)(?:\/|\?|$)/.test(path))
    return `clinics/${path}`;
  return path;
}

function assertCurrentClinic(generation: number) {
  if (generation !== clinicGeneration) throw new DOMException("La clínica activa cambió.", "AbortError");
}

export class ApiError extends Error {
  status: number;
  payload: Record<string, unknown> | null;

  constructor(message: string, status: number, payload: Record<string, unknown> | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function getFormErrors<T extends string>(error: unknown): FieldErrors<T> {
  if (error instanceof ApiError && error.payload) return error.payload as FieldErrors<T>;
  return { detail: error instanceof Error ? error.message : "No fue posible completar la operación." } as FieldErrors<T>;
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "No fue posible completar la operación.";
}

export function setAccessToken(token: string | null) {
  if (token !== accessToken) pendingReads.clear();
  accessToken = token;
  if (!token) setClinicContext(null);
}

export function getAccessToken() { return accessToken; }

export async function waitForAuthRefresh(): Promise<void> {
  if (refreshPromise) await refreshPromise;
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = fetch("/api/v1/auth/refresh/", { method: "POST", credentials: "include" })
      .then(async (response) => {
        if (!response.ok) return null;
        const payload = await response.json() as { access: string };
        setAccessToken(payload.access);
        return payload.access;
      })
      .catch(() => null)
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

async function apiResponse(path: string, options: RequestInit = {}): Promise<Response> {
  const generation = clinicGeneration;
  const controller = new AbortController();
  const externalSignal = options.signal;
  const abort = () => controller.abort();
  if (externalSignal?.aborted) controller.abort();
  else externalSignal?.addEventListener("abort", abort, { once: true });
  inFlightRequests.add(controller);
  try {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (clinicId && !headers.has("X-Clinic-ID")) headers.set("X-Clinic-ID", clinicId);
  const request = () => fetch(`/api/v1/${clinicPath(path)}`, { ...options, signal: controller.signal, headers, credentials: "include" });
  let response = await request();
  assertCurrentClinic(generation);
  if (response.status === 401 && !path.startsWith("auth/")) {
    const refreshed = await refreshAccessToken();
    assertCurrentClinic(generation);
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed}`);
      response = await request();
      assertCurrentClinic(generation);
    }
    if (response.status === 401) {
      setAccessToken(null);
      window.dispatchEvent(new Event("smile:auth-expired"));
    }
  }
  if (!response.ok) {
    const payload = response.headers.get("content-type")?.includes("application/json")
      ? await response.json() as Record<string, unknown> : null;
    throw new ApiError(typeof payload?.detail === "string" ? payload.detail : "No fue posible completar la operación.", response.status, payload);
  }
  return response;
  } finally {
    inFlightRequests.delete(controller);
    externalSignal?.removeEventListener("abort", abort);
  }
}

export async function api<T = void>(path: string, options: RequestInit = {}): Promise<T> {
  const read = async (): Promise<T> => {
    const generation = clinicGeneration;
    const response = await apiResponse(path, options);
    const contentType = response.headers.get("content-type") || "";
    const payload: Record<string, unknown> | null = contentType.includes("application/json")
      ? await response.json() as Record<string, unknown>
      : null;
    assertCurrentClinic(generation);
    return payload as T;
  };
  // Requests with headers, cancellation, or other options may have different semantics.
  if (Object.keys(options).length !== 0) {
    if (options.method && !["GET", "HEAD"].includes(options.method.toUpperCase())) pendingReads.clear();
    return read();
  }
  const existing = pendingReads.get(path);
  if (existing) return existing as Promise<T>;
  const pending = read();
  pendingReads.set(path, pending);
  try { return await pending; }
  finally { if (pendingReads.get(path) === pending) pendingReads.delete(path); }
}

export async function downloadApiFile(path: string, filename: string): Promise<void> {
  const generation = clinicGeneration;
  const response = await apiResponse(path);
  const disposition = response.headers.get("Content-Disposition") || "";
  const serverName = disposition.match(/filename="([^"]+)"|filename=([^;]+)/i);
  const blob = await response.blob();
  assertCurrentClinic(generation);
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = serverName?.[1] || serverName?.[2]?.trim() || filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
}

export async function apiBlob(path: string, signal?: AbortSignal): Promise<Blob> {
  const generation = clinicGeneration;
  const response = await apiResponse(path, { signal });
  const blob = await response.blob();
  assertCurrentClinic(generation);
  return blob;
}
