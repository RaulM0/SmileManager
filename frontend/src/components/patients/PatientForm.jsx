import { useState } from 'react'

const emptyPatient = { nombre:'', appat:'', apmat:'', fecha_nacimiento:'', genero:'', telefono:'', email:'', estatus:'A' }

export default function PatientForm({ initialValue=emptyPatient, onSubmit, submitLabel='Guardar' }) {
  const [values,setValues]=useState({...emptyPatient,...initialValue}); const [errors,setErrors]=useState({}); const [saving,setSaving]=useState(false)
  async function submit(event){event.preventDefault();setSaving(true);setErrors({});try{await onSubmit(values)}catch(error){setErrors(error.payload||{detail:[error.message]})}finally{setSaving(false)}}
  const field=(name)=>(event)=>setValues({...values,[name]:event.target.value})
  const errorFor=name=>errors[name]&&<div className="invalid-feedback d-block">{errors[name].join?.(' ')||errors[name]}</div>
  return <form onSubmit={submit} className="card border-0 shadow-sm"><div className="card-body p-4"><div className="row g-3">
    <div className="col-md-4"><label htmlFor="nombre" className="form-label">Nombre</label><input id="nombre" className="form-control" required maxLength="50" value={values.nombre} onChange={field('nombre')}/>{errorFor('nombre')}</div>
    <div className="col-md-4"><label htmlFor="appat" className="form-label">Apellido paterno</label><input id="appat" className="form-control" required maxLength="50" value={values.appat} onChange={field('appat')}/>{errorFor('appat')}</div>
    <div className="col-md-4"><label htmlFor="apmat" className="form-label">Apellido materno</label><input id="apmat" className="form-control" required maxLength="50" value={values.apmat} onChange={field('apmat')}/>{errorFor('apmat')}</div>
    <div className="col-md-4"><label htmlFor="fecha_nacimiento" className="form-label">Fecha de nacimiento</label><input id="fecha_nacimiento" type="date" className="form-control" required value={values.fecha_nacimiento} onChange={field('fecha_nacimiento')}/>{errorFor('fecha_nacimiento')}</div>
    <div className="col-md-4"><label htmlFor="genero" className="form-label">Género</label><select id="genero" className="form-select" required value={values.genero} onChange={field('genero')}><option value="">Seleccione</option><option value="M">Masculino</option><option value="F">Femenino</option></select>{errorFor('genero')}</div>
    <div className="col-md-4"><label htmlFor="estatus" className="form-label">Estatus</label><select id="estatus" className="form-select" value={values.estatus} onChange={field('estatus')}><option value="A">Activo</option><option value="I">Inactivo</option></select></div>
    <div className="col-md-6"><label htmlFor="telefono" className="form-label">Teléfono</label><input id="telefono" className="form-control" required pattern="\d{10}" maxLength="10" value={values.telefono} onChange={field('telefono')}/>{errorFor('telefono')}</div>
    <div className="col-md-6"><label htmlFor="email" className="form-label">Correo electrónico</label><input id="email" type="email" className="form-control" required value={values.email} onChange={field('email')}/>{errorFor('email')}</div>
  </div>{errors.detail&&<div className="alert alert-danger mt-3">{errors.detail.join?.(' ')||errors.detail}</div>}<div className="mt-4"><button disabled={saving} className="btn btn-primary px-4">{saving?<span className="spinner-border spinner-border-sm"/>:submitLabel}</button></div></div></form>
}
