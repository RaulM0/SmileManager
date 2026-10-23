import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import PatientForm from '../../components/patients/PatientForm'

export default function PatientCreatePage(){const navigate=useNavigate();return <div className="container py-4"><h1 className="h2 mb-4">Registrar paciente</h1><PatientForm submitLabel="Registrar paciente" onSubmit={async values=>{const patient=await api('patients/',{method:'POST',body:JSON.stringify(values)});navigate(`/patients/${patient.id}`)}}/></div>}
