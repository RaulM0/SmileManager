import { useQueryClient } from "@tanstack/react-query";
import { patientsService } from "../../services/patients";
import { queryKeys } from "../../query/keys";
import { useToast } from "../../context/ToastContext";
import PatientForm from "../../components/patients/PatientForm";

export default function PatientCreatePage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header"><div><h1>Registrar paciente</h1></div></div>
      <PatientForm
        submitLabel="Registrar paciente"
        onSubmit={async (values) => {
          const patient = await patientsService.create(values);
          queryClient.setQueryData(queryKeys.resource(`patients/${patient.id}/`), patient);
          await Promise.all([
            queryClient.invalidateQueries({ queryKey: queryKeys.patients }),
            queryClient.invalidateQueries({ queryKey: queryKeys.resource("dashboard/") }),
          ]);
          toast.success("Paciente registrado correctamente.");
          return `/patients/${patient.id}`;
        }}
      />
    </div>
  );
}
