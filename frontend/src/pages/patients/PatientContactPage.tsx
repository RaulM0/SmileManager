import { useState } from "react";
import type { FormEvent } from "react";
import { getErrorMessage, getFormErrors } from "../../api/client";
import PatientSelector from "../../components/patients/PatientSelector";
import type { FieldErrors, PatientOption } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { patientsService } from "../../services/patients";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";

export default function PatientContactPage() {
  const toast = useToast();
  const [patient, setPatient] = useState<PatientOption | null>(null);
  const [form, setForm] = useState({ asunto: "", mensaje: "" });
  const [baseline, setBaseline] = useState(() => JSON.stringify(form));
  const guard = useUnsavedChanges(JSON.stringify(form) !== baseline);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors<"asunto" | "mensaje">>({});
  const [sending, setSending] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (sending || !patient) return;
    setSending(true);
    setFieldErrors({});
    try {
      const result = await patientsService.email(patient.id, form);
      setBaseline(JSON.stringify(form));
      toast.success(result.detail);
    } catch (err) {
      setFieldErrors(getFormErrors(err));
      toast.error(getErrorMessage(err));
    } finally {
      setSending(false);
    }
  }
  const errorText = (name: "asunto" | "mensaje") => {
    const message = fieldErrors[name];
    if (!message) return null;
    return Array.isArray(message) ? message.join(" ") : message;
  };
  const updateField = (name: "asunto" | "mensaje", value: string) => {
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined, detail: undefined }));
  };
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header"><div><h1>Contactar paciente</h1><p className="clinical-page-description">Enviar un mensaje al correo registrado</p></div></div>
      {!patient ? (
        <section className="appointment-step">
          <h2>Selecciona al paciente</h2>
          <p>Busca el expediente al que se enviará el mensaje.</p>
          <div className="appointment-step-content">
          <div className="clinical-form-body">
            <PatientSelector onSelect={setPatient} />
          </div>
          </div>
        </section>
      ) : (
        <form onSubmit={submit} className="clinical-form-surface co-max-w-[900px]">
          <div className="clinical-form-body">
            <div className="appointment-selected-patient"><div><span>Destinatario</span><strong>{patient.text}</strong></div></div>
            <label htmlFor="subject" className="clinical-form-label">
              Asunto
            </label>
            <input
              id="subject"
              required
              className="clinical-form-control"
              aria-invalid={Boolean(fieldErrors.asunto)}
              aria-describedby={fieldErrors.asunto ? "subject-error" : undefined}
              value={form.asunto}
              onChange={(e) => updateField("asunto", e.target.value)}
            />
            {fieldErrors.asunto && (
              <div id="subject-error" className="clinical-form-field-error">{errorText("asunto")}</div>
            )}
            <label htmlFor="message" className="clinical-form-label co-mt-4">
              Mensaje
            </label>
            <textarea
              id="message"
              required
              rows={7}
              className="clinical-form-control"
              aria-invalid={Boolean(fieldErrors.mensaje)}
              aria-describedby={fieldErrors.mensaje ? "message-error" : undefined}
              value={form.mensaje}
              onChange={(e) => updateField("mensaje", e.target.value)}
            />
            {fieldErrors.mensaje && (
              <div id="message-error" className="clinical-form-field-error">{errorText("mensaje")}</div>
            )}
            <div className="clinical-form-actions">
            <button className="clinical-form-submit" disabled={sending}>{sending ? "Enviando…" : "Enviar correo"}</button>
            <button
              type="button"
              className="clinical-action-outline"
              onClick={() => setPatient(null)}
            >
              Cambiar paciente
            </button>
            </div>
          </div>
        </form>
      )}
    {guard.prompt}</div>
  );
}
