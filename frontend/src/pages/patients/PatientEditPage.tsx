import { useParams } from "react-router-dom";
import { patientsService } from "../../services/patients";
import PatientForm from "../../components/patients/PatientForm";
import { useToast } from "../../context/ToastContext";
import { useResource } from "../../hooks/useResource";
import type { Patient } from "../../types/domain";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../query/keys";

export default function PatientEditPage() {
  const { id } = useParams();
  const toast = useToast();
  const queryClient = useQueryClient();
  const {
    data: patient,
    error: loadError,
    reload,
  } = useResource<Patient>(`clinics/patients/${id}/`);
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
          <h1>Editar paciente</h1>
        </div>
      </div>
      <PatientForm
        key={id}
        initialValue={patient}
        submitLabel="Guardar cambios"
        onSubmit={async (values) => {
          const updated = await patientsService.update(id!, values);
          queryClient.setQueryData(
            queryKeys.resource(`clinics/patients/${id}/`),
            updated,
          );
          await Promise.all([
            queryClient.invalidateQueries({ queryKey: queryKeys.patients }),
            queryClient.invalidateQueries({
              queryKey: queryKeys.resource("clinics/dashboard/"),
            }),
          ]);
          toast.success("Datos del paciente actualizados.");
          return `/patients/${id}`;
        }}
      />
    </div>
  );
}
