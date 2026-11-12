import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { ReactNode } from "react";

type ToastKind = "success" | "error" | "warning" | "info";
type Toast = { id: number; kind: ToastKind; message: string };
type ToastContextValue = {
  success: (message: string) => void;
  error: (message: string) => void;
  warning: (message: string) => void;
  info: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

function ToastItem({ toast, dismiss }: { toast: Toast; dismiss: (id: number) => void }) {
  useEffect(() => {
    const timer = window.setTimeout(() => dismiss(toast.id), toast.kind === "error" || toast.kind === "warning" ? 8000 : 5000);
    return () => window.clearTimeout(timer);
  }, [toast.id, toast.kind, dismiss]);

  return (
    <div className={`clinical-toast is-${toast.kind}`} role={toast.kind === "error" || toast.kind === "warning" ? "alert" : "status"}>
      <i className={`bi ${toast.kind === "success" ? "bi-check-circle" : toast.kind === "error" ? "bi-exclamation-circle" : toast.kind === "warning" ? "bi-exclamation-triangle" : "bi-info-circle"}`} aria-hidden="true" />
      <span>{toast.message}</span>
      <button type="button" onClick={() => dismiss(toast.id)} aria-label="Cerrar notificación"><i className="bi bi-x-lg" aria-hidden="true" /></button>
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [dialog, setDialog] = useState<Element | null>(null);
  useEffect(() => {
    const update = () => setDialog(document.querySelector("dialog[open]"));
    update();
    const observer = new MutationObserver(update);
    observer.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["open"] });
    return () => observer.disconnect();
  }, []);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(0);
  const dismiss = useCallback((id: number) => setToasts((current) => current.filter((toast) => toast.id !== id)), []);
  const notify = useCallback((kind: ToastKind, message: string) => {
    setToasts((current) => [
      ...(kind === "success" ? current.filter((toast) => toast.kind !== "error" && toast.kind !== "warning") : current).slice(-2),
      { id: ++nextId.current, kind, message },
    ]);
  }, []);
  const value = useMemo<ToastContextValue>(() => ({
    success: (message) => notify("success", message),
    error: (message) => notify("error", message),
    warning: (message) => notify("warning", message),
    info: (message) => notify("info", message),
  }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(<div className="clinical-toast-viewport" aria-label="Notificaciones">
        {toasts.map((toast) => <ToastItem key={toast.id} toast={toast} dismiss={dismiss} />)}
      </div>, dialog || document.body)}
    </ToastContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("ToastProvider no está disponible.");
  return context;
}
