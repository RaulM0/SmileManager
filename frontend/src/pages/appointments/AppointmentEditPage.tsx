import { useParams } from "react-router-dom";
import { appointmentsService } from "../../services/appointments";
import AppointmentForm from "../../components/appointments/AppointmentForm";
import { useToast } from "../../context/ToastContext";
import { useResource } from "../../hooks/useResource";
import type { Appointment } from "../../types/domain";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../query/keys";

export default function AppointmentEditPage() {
  const { id } = useParams();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { data: item, error, reload } = useResource<Appointment>(`appointments/${id}/`);
  if (error)
    return <div className="workspace-page co-mx-auto co-max-w-[1320px]"><div className="workspace-inline-error" role="alert">{error}</div><button className="clinical-action-outline co-mt-3" onClick={reload}>Reintentar</button></div>;
  if (!item)
    return (
      <div className="page-loader" role="status" aria-label="Cargando cita">
        <div className="workspace-loader-spinner" />
      </div>
    );
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header"><div><h1>Editar cita #{item.id}</h1><p className="clinical-page-description">{item.paciente.full_name}</p></div></div>
      <AppointmentForm
        key={id}
        initialValue={{ ...item, hora: item.hora.slice(0, 5) }}
        submitLabel="Guardar cambios"
        onSubmit={async (form) => {
          const updated = await appointmentsService.update(id!, item.paciente.id, form);
          queryClient.setQueryData(queryKeys.resource(`appointments/${id}/`), updated);
          await Promise.all([
            queryClient.invalidateQueries({ queryKey: queryKeys.appointments }),
            queryClient.invalidateQueries({ queryKey: queryKeys.resource("dashboard/") }),
          ]);
          toast.success("Cita actualizada correctamente.");
          return `/appointments/${id}`;
        }}
      />
    </div>
  );
}
