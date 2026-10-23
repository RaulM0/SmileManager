import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import PatientForm from "../../components/patients/PatientForm";

export default function PatientEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  useEffect(() => {
    api(`patients/${id}/`).then(setPatient);
  }, [id]);
  if (!patient)
    return (
      <div className="page-loader">
        <div className="spinner-border text-primary" />
      </div>
    );
  return (
    <div className="container py-4">
      <h1 className="h2 mb-4">Editar paciente</h1>
      <PatientForm
        initialValue={patient}
        submitLabel="Guardar cambios"
        onSubmit={async (values) => {
          await api(`patients/${id}/`, {
            method: "PATCH",
            body: JSON.stringify(values),
          });
          navigate(`/patients/${id}`);
        }}
      />
    </div>
  );
}
