import { useNavigate } from "react-router-dom";
import PatientSelector from "../../components/patients/PatientSelector";

export default function ClinicalRecordSelectPage() {
  const navigate = useNavigate();
  return (
    <div className="container py-4">
      <h1 className="h2 mb-4">Historial médico</h1>
      <div className="card border-0 shadow-sm">
        <div className="card-body p-4">
          <PatientSelector
            onSelect={(patient) => navigate(`/patients/${patient.id}/record`)}
          />
        </div>
      </div>
    </div>
  );
}
