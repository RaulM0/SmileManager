import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { appointmentsService } from "../../services/appointments";
import { queryKeys } from "../../query/keys";
import PatientSelector from "../../components/patients/PatientSelector";
import AppointmentForm from "../../components/appointments/AppointmentForm";
import type { PatientOption } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { patientsService } from "../../services/patients";
import { ConfirmDialog } from "../../components/ConfirmDialog";

const initial = {
  fecha: "",
  hora: "",
  motivo: "",
  estatus: "P",
  observaciones: "",
};
export default function AppointmentCreatePage() {
  const [selectedPatient, setSelectedPatient] = useState<PatientOption | null>(
    null,
  );
  const [ignorePreselected, setIgnorePreselected] = useState(false);
  const [hasDraft, setHasDraft] = useState(false);
  const [confirmChange, setConfirmChange] = useState(false);
  const [params] = useSearchParams();
  const patientId = params.get("patient") || "";
  const preselected = useQuery({
    queryKey: queryKeys.resource(`clinics/patients/${patientId}/`),
    queryFn: () => patientsService.get(patientId),
    enabled: /^\d+$/.test(patientId) && !ignorePreselected,
  });
  const patient =
    selectedPatient ??
    (!ignorePreselected && preselected.data
      ? {
          id: preselected.data.id,
          text: [
            preselected.data.nombre,
            preselected.data.appat,
            preselected.data.apmat,
          ]
            .filter(Boolean)
            .join(" "),
        }
      : null);
  const toast = useToast();
  const queryClient = useQueryClient();
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>Nueva cita</h1>
        </div>
      </div>
      {patientId &&
        !ignorePreselected &&
        preselected.isFetching &&
        !patient && <p role="status">Cargando paciente…</p>}
      {patientId && !ignorePreselected && preselected.error && (
        <p className="workspace-inline-error" role="alert">
          No se pudo cargar el paciente. Busca y selecciona uno para continuar.
        </p>
      )}
      {!patient ? (
        <section className="appointment-step">
          <h2>1. Selecciona al paciente</h2>
          <p>Busca el expediente al que se asociará esta cita.</p>
          <div className="appointment-step-content">
            <div className="clinical-form-body">
              <PatientSelector
                onSelect={(value) => {
                  setIgnorePreselected(true);
                  setSelectedPatient(value);
                }}
              />
            </div>
          </div>
        </section>
      ) : (
        <>
          <div className="appointment-selected-patient">
            <div>
              <span>Paciente seleccionado</span>
              <strong>{patient.text}</strong>
            </div>
            <button
              className="clinical-action-outline clinical-action-compact"
              onClick={() => {
                if (hasDraft) setConfirmChange(true);
                else {
                  setSelectedPatient(null);
                  setIgnorePreselected(true);
                }
              }}
            >
              Cambiar
            </button>
          </div>
          <AppointmentForm
            initialValue={initial}
            onDirtyChange={setHasDraft}
            submitLabel="Registrar cita"
            onSubmit={async (form) => {
              const result = await appointmentsService.create(patient.id, form);
              queryClient.setQueryData(
                queryKeys.resource(`clinics/appointments/${result.id}/`),
                result,
              );
              await Promise.all([
                queryClient.invalidateQueries({
                  queryKey: queryKeys.appointments,
                }),
                queryClient.invalidateQueries({
                  queryKey: queryKeys.resource("clinics/dashboard/"),
                }),
              ]);
              toast.success("Cita registrada correctamente.");
              return `/appointments/${result.id}`;
            }}
          />
        </>
      )}
      {confirmChange && (
        <ConfirmDialog
          title="Cambiar paciente"
          confirmLabel="Descartar cambios"
          busy={false}
          onClose={() => setConfirmChange(false)}
          onConfirm={() => {
            setConfirmChange(false);
            setSelectedPatient(null);
            setIgnorePreselected(true);
            setHasDraft(false);
          }}
        >
          <p>
            Al cambiar de paciente se descartarán los datos de la cita que aún
            no has guardado.
          </p>
        </ConfirmDialog>
      )}
    </div>
  );
}
