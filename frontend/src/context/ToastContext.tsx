import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

type ToastKind = "success" | "error" | "info";
type Toast = { id: number; kind: ToastKind; message: string };
type ToastContextValue = {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

function ToastItem({ toast, dismiss }: { toast: Toast; dismiss: (id: number) => void }) {
  useEffect(() => {
    const timer = window.setTimeout(() => dismiss(toast.id), toast.kind === "error" ? 8000 : 5000);
    return () => window.clearTimeout(timer);
  }, [toast.id, toast.kind, dismiss]);

  return (
    <div className={`clinical-toast is-${toast.kind}`} role={toast.kind === "error" ? "alert" : "status"}>
      <i className={`bi ${toast.kind === "success" ? "bi-check-circle" : toast.kind === "error" ? "bi-exclamation-circle" : "bi-info-circle"}`} aria-hidden="true" />
      <span>{toast.message}</span>
      <button type="button" onClick={() => dismiss(toast.id)} aria-label="Cerrar notificación"><i className="bi bi-x-lg" aria-hidden="true" /></button>
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(0);
  const dismiss = useCallback((id: number) => setToasts((current) => current.filter((toast) => toast.id !== id)), []);
  const notify = useCallback((kind: ToastKind, message: string) => {
    setToasts((current) => [
      ...(kind === "success" ? current.filter((toast) => toast.kind !== "error") : current).slice(-2),
      { id: ++nextId.current, kind, message },
    ]);
  }, []);
  const value = useMemo<ToastContextValue>(() => ({
    success: (message) => notify("success", message),
    error: (message) => notify("error", message),
    info: (message) => notify("info", message),
  }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="clinical-toast-viewport" aria-label="Notificaciones">
        {toasts.map((toast) => <ToastItem key={toast.id} toast={toast} dismiss={dismiss} />)}
      </div>
    </ToastContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("ToastProvider no está disponible.");
  return context;
}
