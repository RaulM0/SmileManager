import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ChangeEvent, FormEvent } from "react";
import { getFormErrors } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import type { AppointmentFormValues, FieldErrors } from "../../types/domain";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";

type AppointmentField = keyof AppointmentFormValues;

interface AppointmentFormProps {
  initialValue: AppointmentFormValues;
  onSubmit: (values: AppointmentFormValues) => Promise<string>;
  submitLabel: string;
  onDirtyChange?: (dirty: boolean) => void;
}

export default function AppointmentForm({
  initialValue,
  onSubmit,
  submitLabel,
  onDirtyChange,
}: AppointmentFormProps) {
  const toast = useToast();
  const [form, setForm] = useState<AppointmentFormValues>(initialValue);
  const initial = useRef(JSON.stringify(form));
  const dirty = JSON.stringify(form) !== initial.current;
  const guard = useUnsavedChanges(dirty);
  useEffect(() => { onDirtyChange?.(dirty); }, [dirty, onDirtyChange]);
  const navigate = useNavigate();
  const [errors, setErrors] = useState<FieldErrors<AppointmentField>>({});
  const [saving, setSaving] = useState(false);
  const set = (name: AppointmentField) => (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm({ ...form, [name]: e.target.value });
    setErrors((current) => ({ ...current, [name]: undefined, detail: undefined }));
  };
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setErrors({});
    try {
      const destination = await onSubmit(form);
      guard.markSaved();
      navigate(destination);
    } catch (error) {
      const nextErrors = getFormErrors<AppointmentField>(error);
      setErrors(nextErrors);
      const detail = nextErrors.detail;
      toast.error(Array.isArray(detail) ? detail.join(" ") : detail || "Revisa los campos de la cita.");
    } finally {
      setSaving(false);
    }
  }
  const errorText = (name: AppointmentField | "detail") => {
    const message = errors[name];
    if (!message) return null;
    return Array.isArray(message) ? message.join(" ") : message;
  };
  return (
    <><form onSubmit={submit} className="clinical-form-surface"><fieldset className="clinical-form-fieldset" disabled={saving}>
      <div className="clinical-form-body">
        <p className="clinical-form-help">Fecha y hora son obligatorias; motivo y observaciones son opcionales.</p>
        <h2 className="form-section-heading">Programación</h2>
        <div className="clinical-form-grid">
          <div className="clinical-form-col-6">
            <label htmlFor="fecha" className="clinical-form-label">
              Fecha
            </label>
            <input
              id="fecha"
              type="date"
              required
              className="clinical-form-control"
              aria-invalid={Boolean(errors.fecha)}
              aria-describedby={errors.fecha ? "fecha-error" : undefined}
              value={form.fecha}
              onChange={set("fecha")}
            />
            {errors.fecha && (
              <div id="fecha-error" className="clinical-form-field-error">{errorText("fecha")}</div>
            )}
          </div>
          <div className="clinical-form-col-6">
            <label htmlFor="hora" className="clinical-form-label">
              Hora
            </label>
            <input
              id="hora"
              type="time"
              required
              className="clinical-form-control"
              aria-invalid={Boolean(errors.hora)}
              aria-describedby={errors.hora ? "hora-error" : undefined}
              value={form.hora}
              onChange={set("hora")}
            />
            {errors.hora && (
              <div id="hora-error" className="clinical-form-field-error">{errorText("hora")}</div>
            )}
          </div>
          <div className="clinical-form-col-6">
            <label htmlFor="estatus" className="clinical-form-label">
              Estado
            </label>
            <select
              id="estatus"
              className="clinical-form-control"
              aria-invalid={Boolean(errors.estatus)}
              aria-describedby={errors.estatus ? "estatus-error" : undefined}
              value={form.estatus}
              onChange={set("estatus")}
            >
              <option value="P">Pendiente</option>
              <option value="C">Completada</option>
              <option value="A">Cancelada</option>
            </select>
            {errors.estatus && (
              <div id="estatus-error" className="clinical-form-field-error">{errorText("estatus")}</div>
            )}
          </div>
        </div>
        <section className="form-section">
          <h2 className="form-section-heading">Motivo y notas</h2>
          <div className="clinical-form-grid">
          <div className="clinical-form-col-full">
            <label htmlFor="motivo" className="clinical-form-label">
              Motivo
            </label>
            <textarea
              id="motivo"
              className="clinical-form-control"
              rows={3}
              aria-invalid={Boolean(errors.motivo)}
              aria-describedby={errors.motivo ? "motivo-error" : undefined}
              value={form.motivo}
              onChange={set("motivo")}
            />
            {errors.motivo && (
              <div id="motivo-error" className="clinical-form-field-error">{errorText("motivo")}</div>
            )}
          </div>
          <div className="clinical-form-col-full">
            <label htmlFor="observaciones" className="clinical-form-label">
              Observaciones
            </label>
            <textarea
              id="observaciones"
              className="clinical-form-control"
              rows={3}
              aria-invalid={Boolean(errors.observaciones)}
              aria-describedby={errors.observaciones ? "observaciones-error" : undefined}
              value={form.observaciones}
              onChange={set("observaciones")}
            />
            {errors.observaciones && (
              <div id="observaciones-error" className="clinical-form-field-error">{errorText("observaciones")}</div>
            )}
          </div>
          </div>
        </section>
        <div className="clinical-form-actions">
          <button disabled={saving} className="clinical-form-submit">
            {saving ? (
              <>
                <span className="clinical-form-spinner co-mr-2" aria-hidden="true" />
                Guardando…
              </>
            ) : (
              submitLabel
            )}
          </button>
        </div>
      </div>
    </fieldset></form>{guard.prompt}</>
  );
}
