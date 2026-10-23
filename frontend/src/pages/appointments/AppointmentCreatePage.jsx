import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import PatientSelector from "../../components/patients/PatientSelector";
import AppointmentForm from "../../components/appointments/AppointmentForm";

const initial = {
  fecha: "",
  hora: "",
  motivo: "",
  estatus: "P",
  observaciones: "",
};
export default function AppointmentCreatePage() {
  const [patient, setPatient] = useState(null);
  const navigate = useNavigate();
  return (
    <div className="container py-4">
      <h1 className="h2 mb-4">Nueva cita</h1>
      {!patient ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body p-4">
            <PatientSelector onSelect={setPatient} />
          </div>
        </div>
      ) : (
        <>
          <div className="alert alert-info">
            Paciente: <strong>{patient.text}</strong>{" "}
            <button
              className="btn btn-sm btn-link"
              onClick={() => setPatient(null)}
            >
              Cambiar
            </button>
          </div>
          <AppointmentForm
            initialValue={initial}
            submitLabel="Registrar cita"
            onSubmit={async (form) => {
              const result = await api("appointments/", {
                method: "POST",
                body: JSON.stringify({ ...form, paciente_id: patient.id }),
              });
              navigate(`/appointments/${result.id}`);
            }}
          />
        </>
      )}
    </div>
  );
}
