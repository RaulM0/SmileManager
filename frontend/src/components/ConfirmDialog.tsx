import { useEffect, useRef } from "react";

export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  busy,
  busyLabel = "Procesando…",
  variant = "danger",
  onConfirm,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  confirmLabel: string;
  busy: boolean;
  busyLabel?: string;
  variant?: "danger" | "primary";
  onConfirm: () => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog
      ref={ref}
      className="clinical-confirm-dialog"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <h2 id="confirm-dialog-title">{title}</h2>
      <div id="confirm-dialog-description">{children}</div>
      <div className="clinical-confirm-actions">
        <button
          type="button"
          className="clinical-action-outline"
          onClick={onClose}
          disabled={busy}
          autoFocus
        >
          Volver
        </button>
        <button
          type="button"
          className={
            variant === "primary"
              ? "clinical-action-primary"
              : "clinical-action-danger"
          }
          onClick={onConfirm}
          disabled={busy}
        >
          {busy ? busyLabel : confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
