import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getErrorMessage, getFormErrors } from "../../api/client";
import type { Consultation, FieldErrors, Paginated } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { useResource } from "../../hooks/useResource";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../query/keys";
import { imagesService } from "../../services/images";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";

type UploadForm = { consulta_id: string; tipo_imagen: string; descripcion: string; imagen: File | null };

export default function ClinicalImageUploadPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [consultationPage, setConsultationPage] = useState(1);
  const { data: consultationData, error: consultationError, loading: consultationsLoading, reload } = useResource<Paginated<Consultation>>(`clinics/patients/${id}/consultations/?page=${consultationPage}`);
  const consultations = consultationData?.results;
  const [form, setForm] = useState<UploadForm>({
    consulta_id: "",
    tipo_imagen: "",
    descripcion: "",
    imagen: null,
  });
  const guard = useUnsavedChanges(Object.values(form).some(Boolean));
  const [errors, setErrors] = useState<FieldErrors<"consulta_id" | "tipo_imagen" | "descripcion" | "imagen">>({});
  const [saving, setSaving] = useState(false);
  const errorText = (name: keyof UploadForm) => {
    const message = errors[name];
    if (!message) return null;
    return Array.isArray(message) ? message.join(" ") : message;
  };
  const updateField = <K extends keyof UploadForm>(name: K, value: UploadForm[K]) => {
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined, detail: undefined }));
  };
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (saving) return;
    setSaving(true);
    setErrors({});
    const data = new FormData();
    Object.entries(form).forEach(([key, value]) => { if (value !== null) data.append(key, value); });
    try {
      await imagesService.upload(id!, data);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.images(id!) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.diagnostics }),
      ]);
      toast.success("Imagen clínica guardada.");
      guard.markSaved();
      navigate(`/patients/${id}/images/history`);
    } catch (error) {
      setErrors(getFormErrors(error));
      toast.error(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header"><div><h1>Cargar imagen clínica</h1></div></div>
      {consultationError && <div className="workspace-inline-error" role="alert">{consultationError}<button className="clinical-action-outline co-ml-3" onClick={reload}>Reintentar</button></div>}
      {consultationsLoading && <div className="clinical-loading-note" role="status">Cargando consultas…</div>}
      <form onSubmit={submit} className="clinical-form-surface co-max-w-[900px]"><fieldset className="clinical-form-fieldset" disabled={saving}>
        <div className="clinical-form-body">
          <p className="clinical-form-help">Todos los campos son obligatorios.</p>
          <div className="clinical-form-field">
            <label htmlFor="consulta" className="clinical-form-label">
              Consulta
            </label>
            <select
              id="consulta"
              required
              className="clinical-form-control"
              aria-invalid={Boolean(errors.consulta_id)}
              aria-describedby={errors.consulta_id ? "consulta-error" : undefined}
              value={form.consulta_id}
              onChange={(e) => updateField("consulta_id", e.target.value)}
            >
              <option value="">Seleccione una consulta</option>
                {form.consulta_id && !consultations?.some((c) => String(c.id) === form.consulta_id) && <option value={form.consulta_id}>Consulta seleccionada #{form.consulta_id}</option>}
              {(consultations ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {new Date(c.fecha_consulta).toLocaleString("es-MX")} —{" "}
                  {c.motivo_consulta}
                </option>
              ))}
            </select>
              <div><button type="button" disabled={consultationPage === 1} onClick={() => setConsultationPage(consultationPage - 1)}>Consultas anteriores</button><span> Página {consultationPage} </span><button type="button" disabled={!consultationData?.next} onClick={() => setConsultationPage(consultationPage + 1)}>Más consultas</button></div>
            {errors.consulta_id && (
              <div id="consulta-error" className="clinical-form-field-error">
                {errorText("consulta_id")}
              </div>
            )}
          </div>
          <div className="clinical-form-field">
            <label htmlFor="tipo" className="clinical-form-label">
              Tipo de imagen
            </label>
            <input
              id="tipo"
              required
              className="clinical-form-control"
              aria-invalid={Boolean(errors.tipo_imagen)}
              aria-describedby={errors.tipo_imagen ? "tipo-error" : undefined}
              value={form.tipo_imagen}
              onChange={(e) => updateField("tipo_imagen", e.target.value)}
            />
            {errors.tipo_imagen && (
              <div id="tipo-error" className="clinical-form-field-error">{errorText("tipo_imagen")}</div>
            )}
          </div>
          <div className="clinical-form-field">
            <label htmlFor="descripcion" className="clinical-form-label">
              Descripción
            </label>
            <textarea
              id="descripcion"
              required
              className="clinical-form-control"
              aria-invalid={Boolean(errors.descripcion)}
              aria-describedby={errors.descripcion ? "descripcion-error" : undefined}
              value={form.descripcion}
              onChange={(e) => updateField("descripcion", e.target.value)}
            />
            {errors.descripcion && (
              <div id="descripcion-error" className="clinical-form-field-error">{errorText("descripcion")}</div>
            )}
          </div>
          <div className="clinical-form-field">
            <label htmlFor="imagen" className="clinical-form-label">
              Archivo
            </label>
            <input
              id="imagen"
              required
              type="file"
              accept="image/*"
              className="clinical-form-control"
              aria-invalid={Boolean(errors.imagen)}
              aria-describedby={errors.imagen ? "imagen-error" : undefined}
              onChange={(e) => updateField("imagen", e.target.files?.[0] ?? null)}
            />
            {errors.imagen && (
              <div id="imagen-error" className="clinical-form-field-error">{errorText("imagen")}</div>
            )}
          </div>
          {!consultationsLoading && !consultationError && !consultations?.length && (
            <p className="clinical-form-warning">
              Primero registra una consulta para este paciente. <Link to={`/patients/${id}/consultations/new?continue=images`}>Registrar consulta</Link>
            </p>
          )}
          <div className="clinical-form-actions"><button
            disabled={saving || consultationsLoading || !consultations?.length || Boolean(consultationError)}
            className="clinical-form-submit"
          >
            {saving ? (
              <>
                <span className="clinical-form-spinner" aria-hidden="true" />
                Guardando imagen…
              </>
            ) : (
              "Cargar imagen"
            )}
          </button></div>
        </div>
      </fieldset></form>{guard.prompt}
    </div>
  );
}
