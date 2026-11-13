import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ChangeEvent, FormEvent } from "react";
import { getFormErrors } from "../../api/client";
import { useToast } from "../../context/ToastContext";
import type { FieldErrors, PatientFormValues } from "../../types/domain";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";

const emptyPatient: PatientFormValues = {
  nombre: "",
  appat: "",
  apmat: "",
  fecha_nacimiento: "",
  genero: "",
  telefono: "",
  email: "",
  estatus: "A",
};

type PatientField = keyof PatientFormValues;

interface PatientFormProps {
  initialValue?: Partial<PatientFormValues>;
  onSubmit: (values: PatientFormValues) => Promise<string>;
  submitLabel?: string;
}

export default function PatientForm({
  initialValue = emptyPatient,
  onSubmit,
  submitLabel = "Guardar",
}: PatientFormProps) {
  const toast = useToast();
  const [values, setValues] = useState<PatientFormValues>({
    ...emptyPatient,
    ...initialValue,
  });
  const [initial] = useState(() => JSON.stringify(values));
  const guard = useUnsavedChanges(JSON.stringify(values) !== initial);
  const navigate = useNavigate();
  const [errors, setErrors] = useState<FieldErrors<PatientField>>({});
  const [saving, setSaving] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setErrors({});
    try {
      const destination = await onSubmit(values);
      guard.markSaved();
      navigate(destination);
    } catch (error) {
      const nextErrors = getFormErrors<PatientField>(error);
      setErrors(nextErrors);
      const detail = nextErrors.detail;
      toast.error(
        Array.isArray(detail)
          ? detail.join(" ")
          : detail || "Revisa los datos del paciente.",
      );
    } finally {
      setSaving(false);
    }
  }
  const field =
    (name: PatientField) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setValues({ ...values, [name]: event.target.value });
      setErrors((current) => ({
        ...current,
        [name]: undefined,
        detail: undefined,
      }));
    };
  const errorFor = (name: PatientField) => {
    const message = errors[name];
    if (!message) return null;
    return (
      <div id={`${name}-error`} className="clinical-form-field-error">
        {Array.isArray(message) ? message.join(" ") : message}
      </div>
    );
  };
  return (
    <>
      <form onSubmit={submit} className="clinical-form-surface">
        <fieldset className="clinical-form-fieldset" disabled={saving}>
          <div className="clinical-form-body">
            <p className="clinical-form-help">
              Todos los campos son obligatorios, excepto el estado.
            </p>
            <h2 className="form-section-heading">Datos del paciente</h2>
            <div className="clinical-form-grid">
              <div className="clinical-form-col-4">
                <label htmlFor="nombre" className="clinical-form-label">
                  Nombre
                </label>
                <input
                  id="nombre"
                  className="clinical-form-control"
                  required
                  maxLength={50}
                  aria-invalid={Boolean(errors.nombre)}
                  aria-describedby={errors.nombre ? "nombre-error" : undefined}
                  value={values.nombre}
                  onChange={field("nombre")}
                />
                {errorFor("nombre")}
              </div>
              <div className="clinical-form-col-4">
                <label htmlFor="appat" className="clinical-form-label">
                  Apellido paterno
                </label>
                <input
                  id="appat"
                  className="clinical-form-control"
                  required
                  maxLength={50}
                  aria-invalid={Boolean(errors.appat)}
                  aria-describedby={errors.appat ? "appat-error" : undefined}
                  value={values.appat}
                  onChange={field("appat")}
                />
                {errorFor("appat")}
              </div>
              <div className="clinical-form-col-4">
                <label htmlFor="apmat" className="clinical-form-label">
                  Apellido materno
                </label>
                <input
                  id="apmat"
                  className="clinical-form-control"
                  required
                  maxLength={50}
                  aria-invalid={Boolean(errors.apmat)}
                  aria-describedby={errors.apmat ? "apmat-error" : undefined}
                  value={values.apmat}
                  onChange={field("apmat")}
                />
                {errorFor("apmat")}
              </div>
              <div className="clinical-form-col-4">
                <label
                  htmlFor="fecha_nacimiento"
                  className="clinical-form-label"
                >
                  Fecha de nacimiento
                </label>
                <input
                  id="fecha_nacimiento"
                  type="date"
                  className="clinical-form-control"
                  required
                  aria-invalid={Boolean(errors.fecha_nacimiento)}
                  aria-describedby={
                    errors.fecha_nacimiento
                      ? "fecha_nacimiento-error"
                      : undefined
                  }
                  value={values.fecha_nacimiento}
                  onChange={field("fecha_nacimiento")}
                />
                {errorFor("fecha_nacimiento")}
              </div>
              <div className="clinical-form-col-4">
                <label htmlFor="genero" className="clinical-form-label">
                  Género
                </label>
                <select
                  id="genero"
                  className="clinical-form-control"
                  required
                  aria-invalid={Boolean(errors.genero)}
                  aria-describedby={errors.genero ? "genero-error" : undefined}
                  value={values.genero}
                  onChange={field("genero")}
                >
                  <option value="">Seleccione</option>
                  <option value="M">Masculino</option>
                  <option value="F">Femenino</option>
                </select>
                {errorFor("genero")}
              </div>
              <div className="clinical-form-col-4">
                <label htmlFor="estatus" className="clinical-form-label">
                  Estatus
                </label>
                <select
                  id="estatus"
                  className="clinical-form-control"
                  aria-invalid={Boolean(errors.estatus)}
                  aria-describedby={
                    errors.estatus ? "estatus-error" : undefined
                  }
                  value={values.estatus}
                  onChange={field("estatus")}
                >
                  <option value="A">Activo</option>
                  <option value="I">Inactivo</option>
                </select>
                {errorFor("estatus")}
              </div>
            </div>
            <section
              className="form-section"
              aria-labelledby="patient-contact-heading"
            >
              <h2 id="patient-contact-heading" className="form-section-heading">
                Contacto
              </h2>
              <div className="clinical-form-grid">
                <div className="clinical-form-col-6">
                  <label htmlFor="telefono" className="clinical-form-label">
                    Teléfono
                  </label>
                  <input
                    id="telefono"
                    className="clinical-form-control"
                    required
                    pattern="\d{10}"
                    maxLength={10}
                    aria-invalid={Boolean(errors.telefono)}
                    aria-describedby={
                      errors.telefono
                        ? "telefono-help telefono-error"
                        : "telefono-help"
                    }
                    value={values.telefono}
                    onChange={field("telefono")}
                  />
                  <small id="telefono-help" className="clinical-form-help">
                    Ingresa 10 dígitos, sin espacios.
                  </small>
                  {errorFor("telefono")}
                </div>
                <div className="clinical-form-col-6">
                  <label htmlFor="email" className="clinical-form-label">
                    Correo electrónico
                  </label>
                  <input
                    id="email"
                    type="email"
                    className="clinical-form-control"
                    required
                    aria-invalid={Boolean(errors.email)}
                    aria-describedby={errors.email ? "email-error" : undefined}
                    value={values.email}
                    onChange={field("email")}
                  />
                  {errorFor("email")}
                </div>
              </div>
            </section>
            <div className="clinical-form-actions">
              <button disabled={saving} className="clinical-form-submit">
                {saving ? (
                  <>
                    <span
                      className="clinical-form-spinner co-mr-2"
                      aria-hidden="true"
                    />
                    Guardando…
                  </>
                ) : (
                  submitLabel
                )}
              </button>
            </div>
          </div>
        </fieldset>
      </form>
      {guard.prompt}
    </>
  );
}
