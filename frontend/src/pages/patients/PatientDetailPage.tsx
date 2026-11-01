import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getErrorMessage } from "../../api/client";
import { patientsService } from "../../services/patients";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../query/keys";
import { formatDate } from "../../utils/date";
import { useToast } from "../../context/ToastContext";
import { useResource } from "../../hooks/useResource";
import type { Patient } from "../../types/domain";

export default function PatientDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { data: patient, error, reload } = useResource<Patient>(`patients/${id}/`);
  const [deactivating, setDeactivating] = useState(false);
  async function deactivate() {
    if (deactivating) return;
    if (!window.confirm("¿Deseas desactivar este paciente?")) return;
    setDeactivating(true);
    try {
      const updated = await patientsService.deactivate(id!);
      queryClient.setQueryData(queryKeys.resource(`patients/${id}/`), updated);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.patients }),
        queryClient.invalidateQueries({ queryKey: queryKeys.resource("dashboard/") }),
      ]);
      toast.success("Paciente desactivado.");
      navigate("/patients/search");
    } catch (requestError) {
      toast.error(getErrorMessage(requestError));
      setDeactivating(false);
    }
  }
  if (error)
    return (
      <div className="workspace-page co-mx-auto co-max-w-[1320px]">
        <div className="workspace-inline-error" role="alert">{error}</div>
        <button className="clinical-action-outline co-mt-3" onClick={reload}>Reintentar</button>
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
      <section className="patient-profile" aria-labelledby="patient-name">
        <div className="patient-profile-heading">
          <div>
            <h1 id="patient-name">
              {patient.nombre} {patient.appat} {patient.apmat}
            </h1>
          </div>
          <div className="patient-profile-actions">
          <Link className="clinical-action-outline" to={`/appointments/new?patient=${patient.id}`}>Nueva cita</Link>
          <Link className="clinical-action-primary" to={`/patients/${id}/edit`}>
            Editar
          </Link>
          <button
            className="clinical-action-danger"
            disabled={patient.estatus === "I" || deactivating}
            onClick={deactivate}
          >
            {deactivating ? "Desactivando…" : "Desactivar"}
          </button>
          </div>
        </div>
        <div className="patient-profile-meta">
          <span><i className="bi bi-calendar3" aria-hidden="true" /><time dateTime={patient.fecha_nacimiento}>{formatDate(patient.fecha_nacimiento)}</time> · {patient.age} años</span>
          <span><i className="bi bi-person" aria-hidden="true" />{patient.genero === "F" ? "Femenino" : "Masculino"}</span>
          <span className={`patient-status ${patient.estatus === "A" ? "is-active" : "is-inactive"}`}>{patient.estatus === "A" ? "Activo" : "Inactivo"}</span>
          <span><i className="bi bi-telephone" aria-hidden="true" />{patient.telefono}</span>
          <span><i className="bi bi-envelope" aria-hidden="true" />{patient.email}</span>
        </div>
      </section>
      <div className="co-mt-4"><Link className="clinical-action-outline" to={`/patients/${id}/record`}>Abrir expediente clínico <i className="bi bi-arrow-right" aria-hidden="true" /></Link></div>
    </div>
  );
}
