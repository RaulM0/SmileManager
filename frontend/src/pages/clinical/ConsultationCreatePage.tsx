import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getErrorMessage, getFormErrors } from "../../api/client";
import type { FieldErrors, Patient } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { useResource } from "../../hooks/useResource";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../query/keys";
import { clinicalService } from "../../services/clinical";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";

export default function ConsultationCreatePage() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const {
    data: patient,
    error: loadError,
    reload,
  } = useResource<Patient>(`clinics/patients/${id}/`);
  const [form, setForm] = useState({
    motivo_consulta: "",
    diagnostico: "",
    tratamiento: "",
    observaciones: "",
  });
  const guard = useUnsavedChanges(Object.values(form).some(Boolean));
  const [fieldErrors, setFieldErrors] = useState<
    FieldErrors<keyof typeof form>
  >({});
  const [saving, setSaving] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setFieldErrors({});
    try {
      const result = await clinicalService.createConsultation(id!, form);
      queryClient.setQueryData(
        queryKeys.resource(`clinics/consultations/${result.id}/`),
        result,
      );
      await queryClient.invalidateQueries({
        predicate: (query) =>
          query.queryKey[0] === queryKeys.resource("")[0] &&
          query.queryKey[1] === "resource" &&
          typeof query.queryKey[2] === "string" &&
          query.queryKey[2].startsWith(`clinics/patients/${id}/consultations/`),
      });
      toast.success("Consulta registrada correctamente.");
      guard.markSaved();
      navigate(
        params.get("continue") === "images"
          ? `/patients/${id}/images/upload`
          : `/consultations/${result.id}/prescription`,
      );
    } catch (err) {
      setFieldErrors(getFormErrors(err));
      toast.error(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }
  const errorText = (name: keyof typeof form) => {
    const message = fieldErrors[name];
    if (!message) return null;
    return Array.isArray(message) ? message.join(" ") : message;
  };
  const updateField = (name: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({
      ...current,
      [name]: undefined,
      detail: undefined,
    }));
  };
  if (loadError)
    return (
      <div className="workspace-page co-mx-auto co-max-w-[1320px]">
        <div className="workspace-inline-error" role="alert">
          {loadError}
        </div>
        <button className="clinical-action-outline co-mt-3" onClick={reload}>
          Reintentar
        </button>
      </div>
    );
  if (!patient)
    return (
      <div className="page-loader" role="status" aria-label="Cargando paciente">
        <div className="workspace-loader-spinner" />
      </div>
    );
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>Nueva consulta</h1>
          <p className="clinical-page-description">
            {patient.nombre} {patient.appat}
          </p>
        </div>
      </div>
      <form
        onSubmit={submit}
        className="clinical-form-surface co-max-w-[900px]"
      >
        <fieldset className="clinical-form-fieldset" disabled={saving}>
          <div className="clinical-form-body">
            <p className="clinical-form-help">
              El motivo de consulta es obligatorio; los demás campos son
              opcionales.
            </p>
            {[
              ["motivo_consulta", "Motivo de consulta"],
              ["diagnostico", "Diagnóstico"],
              ["tratamiento", "Tratamiento"],
              ["observaciones", "Observaciones"],
            ].map(([name, label]) => (
              <div className="clinical-form-field" key={name}>
                <label className="clinical-form-label" htmlFor={name}>
                  {label}
                </label>
                <textarea
                  id={name}
                  className="clinical-form-control"
                  rows={3}
                  required={name === "motivo_consulta"}
                  aria-invalid={Boolean(fieldErrors[name as keyof typeof form])}
                  aria-describedby={
                    fieldErrors[name as keyof typeof form]
                      ? `${name}-error`
                      : undefined
                  }
                  value={form[name as keyof typeof form]}
                  onChange={(e) =>
                    updateField(name as keyof typeof form, e.target.value)
                  }
                />
                {fieldErrors[name as keyof typeof form] && (
                  <div
                    id={`${name}-error`}
                    className="clinical-form-field-error"
                  >
                    {errorText(name as keyof typeof form)}
                  </div>
                )}
              </div>
            ))}
            <div className="clinical-form-actions">
              <button className="clinical-form-submit" disabled={saving}>
                {saving ? "Registrando…" : "Registrar consulta"}
              </button>
            </div>
          </div>
        </fieldset>
      </form>
      {guard.prompt}
    </div>
  );
}
