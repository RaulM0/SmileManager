import { useNavigate } from "react-router-dom";
import PatientSelector from "../../components/patients/PatientSelector";

export default function ClinicalRecordSelectPage() {
  const navigate = useNavigate();
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header"><div><h1>Historial médico</h1><p className="clinical-page-description">Selecciona un paciente para abrir su expediente</p></div></div>
      <section className="appointment-step">
        <h2>Buscar paciente</h2>
        <div className="appointment-step-content">
        <div className="clinical-form-body">
          <PatientSelector
            onSelect={(patient) => navigate(`/patients/${patient.id}/record`)}
          />
        </div>
        </div>
      </section>
    </div>
  );
}
