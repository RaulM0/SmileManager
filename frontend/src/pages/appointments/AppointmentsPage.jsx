import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'

const statusLabels = { P: 'Pendiente', C: 'Completada', A: 'Cancelada' }
const statusColors = { P: 'warning', C: 'success', A: 'secondary' }
const weekdays = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function AppointmentCalendar({ appointments }) {
  const [visibleMonth, setVisibleMonth] = useState(() => { const now = new Date(); return new Date(now.getFullYear(), now.getMonth(), 1) })
  const byDate = useMemo(() => appointments.reduce((result, appointment) => {
    ;(result[appointment.fecha] ||= []).push(appointment)
    return result
  }, {}), [appointments])
  const first = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1)
  const gridStart = new Date(first)
  gridStart.setDate(first.getDate() - first.getDay())
  const days = Array.from({ length: 42 }, (_, index) => { const value = new Date(gridStart); value.setDate(gridStart.getDate() + index); return value })
  const title = new Intl.DateTimeFormat('es-MX', { month: 'long', year: 'numeric' }).format(first)
  function move(months) { setVisibleMonth(current => new Date(current.getFullYear(), current.getMonth() + months, 1)) }

  return <section className="card border-0 shadow-sm mb-4" aria-label="Calendario de citas">
    <div className="card-header bg-white d-flex align-items-center justify-content-between py-3">
      <button className="btn btn-sm btn-outline-primary" onClick={() => move(-1)} aria-label="Mes anterior"><i className="bi bi-chevron-left" /></button>
      <div className="text-center"><h2 className="h5 text-capitalize mb-1">{title}</h2><button className="btn btn-sm btn-link p-0" onClick={() => { const now = new Date(); setVisibleMonth(new Date(now.getFullYear(), now.getMonth(), 1)) }}>Hoy</button></div>
      <button className="btn btn-sm btn-outline-primary" onClick={() => move(1)} aria-label="Mes siguiente"><i className="bi bi-chevron-right" /></button>
    </div>
    <div className="table-responsive"><div style={{ minWidth: 760 }}>
      <div className="d-grid text-center fw-semibold border-bottom" style={{ gridTemplateColumns: 'repeat(7, 1fr)' }}>{weekdays.map(day => <div className="py-2" key={day}>{day}</div>)}</div>
      <div className="d-grid" style={{ gridTemplateColumns: 'repeat(7, 1fr)' }}>{days.map(date => {
        const key = localDateKey(date); const outside = date.getMonth() !== visibleMonth.getMonth(); const today = key === localDateKey(new Date())
        return <div className={`border-end border-bottom p-2 ${outside ? 'bg-light text-muted' : ''}`} style={{ minHeight: 105 }} key={key}>
          <div className={`small mb-1 ${today ? 'badge rounded-pill text-bg-primary' : ''}`}>{date.getDate()}</div>
          {(byDate[key] || []).map(item => <Link className={`d-block badge text-bg-${statusColors[item.estatus]} text-decoration-none text-truncate mb-1`} title={`${item.hora.slice(0, 5)} ${item.paciente.full_name}`} to={`/appointments/${item.id}`} key={item.id}>{item.hora.slice(0, 5)} {item.paciente.full_name}</Link>)}
        </div>
      })}</div>
    </div></div>
  </section>
}

export default function AppointmentsPage() {
  const [params, setParams] = useSearchParams(); const status = params.get('status') || ''; const search = params.get('search') || ''
  const [term, setTerm] = useState(search); const [items, setItems] = useState(null)
  const load = useCallback(() => api(`appointments/?status=${status}&search=${encodeURIComponent(search)}`).then(setItems), [status, search])
  useEffect(() => { load() }, [load])
  async function action(id, name) { await api(`appointments/${id}/${name}/`, { method: 'POST' }); await load() }
  function submit(event) { event.preventDefault(); setParams({ ...Object.fromEntries(params), search: term }) }
  function selectStatus(value) { setParams({ ...(search ? { search } : {}), ...(value ? { status: value } : {}) }) }
  return <div className="container py-4">
    <div className="d-flex justify-content-between mb-4"><h1 className="h2">Citas</h1><Link to="/appointments/new" className="btn btn-primary"><i className="bi bi-plus-circle me-2" />Nueva cita</Link></div>
    <div className="d-flex gap-2 mb-3">{[['', 'Todas'], ['P', 'Pendientes'], ['C', 'Completadas'], ['A', 'Canceladas']].map(([value, label]) => <button className={`btn btn-${status === value ? 'primary' : 'outline-primary'}`} key={value} onClick={() => selectStatus(value)}>{label}</button>)}</div>
    <form onSubmit={submit} className="input-group mb-4"><input aria-label="Buscar citas" className="form-control" type="search" value={term} onChange={event => setTerm(event.target.value)} placeholder="Paciente, teléfono o ID" /><button className="btn btn-outline-primary">Buscar</button></form>
    {!items ? <div className="page-loader"><div className="spinner-border text-primary" /></div> : <><AppointmentCalendar appointments={items} /><div className="card border-0 shadow-sm"><div className="table-responsive"><table className="table table-hover mb-0"><thead><tr><th>Fecha</th><th>Hora</th><th>Paciente</th><th>Motivo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{items.map(item => <tr key={item.id}><td>{item.fecha}</td><td>{item.hora.slice(0, 5)}</td><td>{item.paciente.full_name}</td><td>{item.motivo}</td><td>{statusLabels[item.estatus]}</td><td><Link className="btn btn-sm btn-outline-primary me-1" to={`/appointments/${item.id}`}>Ver</Link><Link className="btn btn-sm btn-outline-secondary me-1" to={`/appointments/${item.id}/edit`}>Editar</Link>{item.estatus === 'P' && <><button className="btn btn-sm btn-outline-success me-1" onClick={() => action(item.id, 'complete')}>Completar</button><button className="btn btn-sm btn-outline-danger" onClick={() => action(item.id, 'cancel')}>Cancelar</button></>}</td></tr>)}</tbody></table></div>{!items.length && <div className="p-5 text-center text-muted">No se encontraron citas.</div>}</div></>}
  </div>
}
