import { useEffect, useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { Link, NavLink, Outlet, useParams, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, getErrorMessage } from '../../api/client';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { useAuth } from '../../context/AuthContext';
import type { Paginated } from '../../types/domain';

type User = { id: number; username: string; email: string; is_active: boolean; is_staff: boolean; date_joined: string; last_login: string | null; backoffice_assigned?: boolean; administrative_account?: boolean; patient_count?: number };
type Event = { id: number; timestamp: string; actor_username: string | null; action: string; resource_type: string; resource_id: string; outcome: string; request_id: string };
type Run = { id: number; status: string; requested_at: string; started_at: string; completed_at: string | null; requested_by_id: number | null; model_name: string; model_version: string; failure_category: string; request_id: string; potentially_stale: boolean };
type Dashboard = { users: { active: number; inactive: number }; ai: { running: number; failed: number; stale: number }; patients_active?: number; appointments?: { today: number; upcoming: number }; recent_admin_events: Event[] };
type System = { application: string; database: string; ai: string };

const nav = [['Resumen', '/backoffice', 'bi-grid-1x2'], ['Usuarios', '/backoffice/users', 'bi-people'], ['Pacientes', '/backoffice/patients', 'bi-person-vcard'], ['Citas', '/backoffice/appointments', 'bi-calendar3'], ['Auditoría', '/backoffice/audit', 'bi-journal-text'], ['IA', '/backoffice/ai', 'bi-cpu'], ['Sistema', '/backoffice/system', 'bi-hdd-network']];
const date = (value: string | null) => value ? new Date(value).toLocaleString('es-MX') : '—';

function Load({ pending, error, children }: { pending: boolean; error: Error | null; children: ReactNode }) {
  if (pending) return <p role="status">Cargando información…</p>;
  if (error) return <p role="alert">No fue posible cargar la información. Inténtalo de nuevo.</p>;
  return <>{children}</>;
}

function useAdmin<T>(path: string) {
  return useQuery<T, Error>({ queryKey: ['backoffice', path], queryFn: () => api<T>(`backoffice/${path}`), retry: false });
}

function Pages({ page, setPage, data }: { page: number; setPage: (page: number) => void; data?: Paginated<unknown> }) {
  return <nav aria-label="Paginación" className="workspace-pagination"><button className="clinical-action-outline clinical-action-compact" disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button><span className="workspace-pagination-summary">Página {page} · {data?.count ?? 0} registros</span><button className="clinical-action-outline clinical-action-compact" disabled={!data?.next} onClick={() => setPage(page + 1)}>Siguiente</button></nav>;
}

export function BackofficeLayout() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!open) return undefined;
    sidebarRef.current?.querySelector<HTMLElement>('a[href]')?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') { setOpen(false); toggleRef.current?.focus(); return; }
      if (event.key !== 'Tab') return;
      const links = sidebarRef.current?.querySelectorAll<HTMLElement>('a[href], button:not(:disabled)');
      if (!links?.length) return;
      if (event.shiftKey && document.activeElement === links[0]) { event.preventDefault(); links[links.length - 1].focus(); }
      else if (!event.shiftKey && document.activeElement === links[links.length - 1]) { event.preventDefault(); links[0].focus(); }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);
  if (!user?.can_access_backoffice) return <main className="co-p-8"><h1>Acceso no autorizado</h1><p>No tienes permiso para acceder a esta sección.</p><Link to="/">Volver al inicio</Link></main>;
  return <div className="app-shell workspace-shell">
    <a className="skip-link" href="#backoffice-content">Saltar al contenido</a>
    <header className="workspace-topbar">
      <button ref={toggleRef} className="workspace-menu-toggle" type="button" aria-controls="backoffice-nav" aria-expanded={open} aria-label={open ? 'Cerrar navegación' : 'Abrir navegación'} onClick={() => setOpen(value => !value)}><i className={`bi ${open ? 'bi-x-lg' : 'bi-list'}`} aria-hidden="true" /></button>
      <Link className="workspace-brand co-flex co-items-center" to="/backoffice"><span className="workspace-brand-mark" aria-hidden="true"><i className="bi bi-heart-pulse-fill" /></span><span>SmileManager</span></Link>
      <div className="workspace-context">Administración del sistema</div>
      <div className="workspace-user"><span className="workspace-user-avatar" aria-hidden="true">{user.username.slice(0, 1).toUpperCase()}</span><span className="workspace-user-name">{user.username}</span><Link className="workspace-logout" to="/"><i className="bi bi-arrow-left" aria-hidden="true" /><span>Ir a la aplicación</span></Link></div>
    </header>
    {open && <button type="button" className="workspace-scrim" aria-label="Cerrar navegación" onClick={() => { setOpen(false); toggleRef.current?.focus(); }} />}
    <div className="workspace-body"><aside ref={sidebarRef} id="backoffice-nav" className={`workspace-sidebar${open ? ' is-open' : ''}`} role={open ? 'dialog' : undefined} aria-modal={open ? 'true' : undefined} aria-label="Navegación administrativa">
      <nav aria-label="Administración"><div className="workspace-nav-group"><div className="workspace-nav-label">ADMINISTRACIÓN</div>{nav.map(([label, url, icon]) => <NavLink end={url === '/backoffice'} key={url} to={url} onClick={() => { setOpen(false); toggleRef.current?.focus(); }} className={({ isActive }) => `workspace-nav-link${isActive ? ' is-active' : ''}`}><i className={`bi ${icon}`} aria-hidden="true" /><span>{label}</span></NavLink>)}</div></nav>
      <div className="workspace-sidebar-footer"><span className="workspace-clinic-mark" aria-hidden="true">SM</span><span>SmileManager<br /><small>Administración del sistema</small></span></div>
    </aside><main id="backoffice-content" className="workspace-main co-min-w-0" tabIndex={-1}><div className="workspace-page co-mx-auto co-w-full co-max-w-[1320px]"><Outlet /></div><footer className="workspace-footer"><span>SmileManager</span><Link to="/privacy">Aviso de Privacidad</Link></footer></main></div>
  </div>;
}

export function BackofficeDashboard() {
  const query = useAdmin<Dashboard>('dashboard/');
  const d = query.data;
  return <><div className="workspace-page-header"><div><h1>Resumen del sistema</h1><p className="clinical-page-description">Actividad operativa y acceso de usuarios</p></div></div><Load pending={query.isPending} error={query.error}>{d && <><div className="workspace-summary-strip backoffice-summary-strip" aria-label="Resumen operativo">{[['Usuarios activos', d.users.active], ['Usuarios inactivos', d.users.inactive], ['Pacientes activos', d.patients_active ?? '—'], ['Citas hoy', d.appointments?.today ?? '—'], ['Próximas citas', d.appointments?.upcoming ?? '—'], ['IA en curso', d.ai.running], ['IA fallida', d.ai.failed], ['IA posiblemente detenida', d.ai.stale]].map(([label, count]) => <div key={label}><span>{label}</span><strong>{count}</strong></div>)}</div><section className="workspace-section"><div className="workspace-section-heading"><div><h2>Actividad administrativa reciente</h2><p>Últimos cambios de acceso</p></div><Link to="/backoffice/audit">Ver auditoría <i className="bi bi-arrow-right" aria-hidden="true" /></Link></div>{d.recent_admin_events.length ? <Events events={d.recent_admin_events} /> : <div className="workspace-empty-state"><span>Aún no hay acciones administrativas.</span></div>}</section></>}</Load></>;
}

function Events({ events }: { events: Event[] }) { return <ul className="co-mt-3 co-border co-border-[#dce3e6] co-bg-white co-rounded co-divide-y co-divide-[#e8edef]">{events.map(e => <li key={e.id} className="co-p-4 co-text-sm"><div className="co-flex co-flex-wrap co-justify-between co-gap-2"><strong>{e.action}</strong><time>{date(e.timestamp)}</time></div><p className="co-mt-1">{e.actor_username || 'Sistema'} · {e.resource_type} #{e.resource_id} · {e.outcome}</p><p className="co-text-[#52616a] co-break-all">Solicitud: {e.request_id}</p></li>)}</ul>; }

export function BackofficeUsers() {
  const [page, setPage] = useState(1); const [input, setInput] = useState(''); const [search, setSearch] = useState(''); const [state, setState] = useState('');
  const params = new URLSearchParams({ page: String(page), search, state }); const query = useAdmin<Paginated<User>>(`users/?${params}`);
  function submit(e: FormEvent) { e.preventDefault(); setPage(1); setSearch(input); }
  return <><div className="workspace-page-header"><div><h1>Usuarios</h1><p className="clinical-page-description">Administra las cuentas de SmileManager.</p></div><Link className="clinical-action-primary" to="/backoffice/users/new"><i className="bi bi-person-plus" aria-hidden="true" /> Crear usuario</Link></div><form onSubmit={submit} className="co-flex co-flex-wrap co-gap-3 co-mb-5"><label>Buscar usuario <input className="clinical-form-control" value={input} onChange={e => setInput(e.target.value)} /></label><label>Estado <select className="clinical-form-control" value={state} onChange={e => { setState(e.target.value); setPage(1); }}><option value="">Todos</option><option value="active">Activos</option><option value="inactive">Inactivos</option></select></label><button className="clinical-action-primary co-self-end">Buscar</button></form><Load pending={query.isPending} error={query.error}>{query.data && <>{query.data.results.length ? <ul className="co-bg-white co-border co-border-[#dce3e6] co-rounded co-divide-y">{query.data.results.map(u => <li key={u.id} className="co-p-4 co-flex co-flex-wrap co-justify-between co-gap-2"><div><Link to={`/backoffice/users/${u.id}`} className="co-font-semibold">{u.username}</Link><p className="co-text-sm co-text-[#52616a]">{u.email || 'Sin correo'}</p></div><span>{u.is_active ? 'Activo' : 'Inactivo'}</span></li>)}</ul> : <p>No hay usuarios con este filtro.</p>}<Pages page={page} setPage={setPage} data={query.data} /></>}</Load></>;
}

export function BackofficeUser() {
  const { id } = useParams(); const client = useQueryClient(); const { user: actor } = useAuth(); const [confirm, setConfirm] = useState(false); const [message, setMessage] = useState('');
  const query = useAdmin<User>(`users/${id}/`); const u = query.data;
  const mutation = useMutation({ mutationFn: () => api<User>(`backoffice/users/${id}/${u?.is_active ? 'deactivate' : 'activate'}/`, { method: 'POST' }), onSuccess: async () => { setConfirm(false); setMessage('Estado actualizado.'); await client.invalidateQueries({ queryKey: ['backoffice'] }); }, onError: e => { setConfirm(false); setMessage(getErrorMessage(e)); } });
  return <><Link to="/backoffice/users">Volver a usuarios</Link><Load pending={query.isPending} error={query.error}>{u && <><h1 className="co-text-2xl co-font-semibold co-my-5">{u.username}</h1>{message && <p role="status" className="co-mb-4">{message}</p>}<dl className="co-bg-white co-border co-border-[#dce3e6] co-rounded co-p-5 co-grid co-gap-3"><div><dt>Identificador</dt><dd>{u.id}</dd></div><div><dt>Correo</dt><dd>{u.email || '—'}</dd></div><div><dt>Estado</dt><dd>{u.is_active ? 'Activo' : 'Inactivo'}</dd></div><div><dt>Staff técnico</dt><dd>{u.is_staff ? 'Sí' : 'No'}</dd></div><div><dt>Permiso de backoffice asignado</dt><dd>{u.backoffice_assigned ? 'Sí' : 'No'}</dd></div><div><dt>Creado</dt><dd>{date(u.date_joined)}</dd></div><div><dt>Último acceso</dt><dd>{date(u.last_login)}</dd></div></dl><p className="co-mt-4"><Link to={`/backoffice/patients?doctor=${u.id}`}>Ver pacientes asociados ({u.patient_count ?? "?"})</Link> · <Link to={`/backoffice/audit?actor=${u.id}`}>Ver auditoría</Link></p>{u.administrative_account && <p className="co-mt-4">El estado de esta cuenta administrativa se gestiona fuera del backoffice.</p>}<button className="clinical-action-outline co-mt-5" disabled={actor?.id === u.id || u.administrative_account} onClick={() => setConfirm(true)}>{u.is_active ? 'Desactivar usuario' : 'Activar usuario'}</button>{confirm && <ConfirmDialog title={u.is_active ? 'Desactivar usuario' : 'Activar usuario'} confirmLabel={u.is_active ? 'Desactivar' : 'Activar'} busy={mutation.isPending} onClose={() => setConfirm(false)} onConfirm={() => mutation.mutate()}><p>¿Confirmas el cambio de acceso para {u.username}?</p></ConfirmDialog>}</>}</Load></>;
}

export function BackofficeAudit() {
  const [paramsFromUrl] = useSearchParams();
  const [page, setPage] = useState(1); const [draft, setDraft] = useState({ action: '', resource_type: '', outcome: '', actor: paramsFromUrl.get('actor') || '', from: '', to: '', request_id: '' }); const [filters, setFilters] = useState(draft);
  const params = new URLSearchParams({ page: String(page), ...filters }); const query = useAdmin<Paginated<Event>>(`audit/?${params}`);
  return <><h1 className="co-text-2xl co-font-semibold co-mb-5">Auditoría</h1><form onSubmit={e => { e.preventDefault(); setPage(1); setFilters(draft); }} className="co-grid co-grid-cols-1 sm:co-grid-cols-2 lg:co-grid-cols-4 co-gap-3 co-mb-5">{Object.entries({ action: 'Acción', resource_type: 'Tipo de recurso', outcome: 'Resultado', actor: 'ID de actor', from: 'Desde', to: 'Hasta', request_id: 'ID de solicitud' }).map(([key, label]) => <label key={key}>{label}<input type={key === 'from' || key === 'to' ? 'date' : 'text'} className="clinical-form-control" value={draft[key as keyof typeof draft]} onChange={e => setDraft({ ...draft, [key]: e.target.value })} /></label>)}<button className="clinical-action-primary co-self-end">Aplicar filtros</button></form><Load pending={query.isPending} error={query.error}>{query.data && <>{query.data.results.length ? <Events events={query.data.results} /> : <p>No hay eventos con este filtro.</p>}<Pages page={page} setPage={setPage} data={query.data} /></>}</Load></>;
}

export function BackofficeRuns() {
  const [page, setPage] = useState(1); const [status, setStatus] = useState(''); const [model, setModel] = useState(''); const [failure, setFailure] = useState(''); const [from, setFrom] = useState(''); const [to, setTo] = useState('');
  const params = new URLSearchParams({ page: String(page), status, model_version: model, failure_category: failure, from, to }); const query = useAdmin<Paginated<Run>>(`ai-runs/?${params}`);
  return <><h1 className="co-text-2xl co-font-semibold co-mb-5">Ejecuciones de IA</h1><div className="co-grid co-grid-cols-1 sm:co-grid-cols-2 lg:co-grid-cols-4 co-gap-3 co-mb-5"><label>Estado<select className="clinical-form-control" value={status} onChange={e => { setPage(1); setStatus(e.target.value); }}><option value="">Todos</option><option>RUNNING</option><option>SUCCEEDED</option><option>FAILED</option></select></label>{[[model, setModel, 'Versión del modelo', 'text'], [failure, setFailure, 'Categoría de fallo', 'text'], [from, setFrom, 'Desde', 'date'], [to, setTo, 'Hasta', 'date']].map(([value, setter, label, type]) => <label key={label as string}>{label as string}<input type={type as string} className="clinical-form-control" value={value as string} onChange={e => { setPage(1); (setter as (s: string) => void)(e.target.value); }} /></label>)}</div><Load pending={query.isPending} error={query.error}>{query.data && <>{query.data.results.length ? <ul className="co-bg-white co-border co-border-[#dce3e6] co-rounded co-divide-y">{query.data.results.map(r => <li key={r.id} className="co-p-4 co-flex co-justify-between co-gap-3 co-flex-wrap"><div><Link className="co-font-semibold" to={`/backoffice/ai/${r.id}`}>Ejecución #{r.id}</Link><p className="co-text-sm">{date(r.requested_at)} · {r.model_name}</p></div><span>{r.potentially_stale ? 'Posiblemente detenida' : r.status}</span></li>)}</ul> : <p>No hay ejecuciones de IA con este filtro.</p>}<Pages page={page} setPage={setPage} data={query.data} /></>}</Load></>;
}

export function BackofficeRun() {
  const { id } = useParams(); const q = useAdmin<Run>(`ai-runs/${id}/`); const r = q.data;
  return <><Link to="/backoffice/ai">Volver a IA</Link><Load pending={q.isPending} error={q.error}>{r && <><h1 className="co-text-2xl co-font-semibold co-my-5">Ejecución #{r.id}</h1>{r.potentially_stale && <p className="workspace-inline-warning co-mb-4">La ejecución podría estar detenida. La recuperación requiere el procedimiento operacional con workers detenidos.</p>}<dl className="co-bg-white co-border co-border-[#dce3e6] co-rounded co-p-5 co-grid co-gap-3">{[['Estado', r.status], ['Solicitado', date(r.requested_at)], ['Iniciado', date(r.started_at)], ['Finalizado', date(r.completed_at)], ['Solicitante', r.requested_by_id ?? '—'], ['Modelo', r.model_name], ['Versión', r.model_version], ['Fallo', r.failure_category || '—'], ['Solicitud', r.request_id]].map(([key, value]) => <div key={key}><dt>{key}</dt><dd className="co-break-all">{value}</dd></div>)}</dl></>}</Load></>;
}

export function BackofficeSystem() {
  const q = useAdmin<System>('system/');
  return <><h1 className="co-text-2xl co-font-semibold co-mb-5">Estado del sistema</h1><Load pending={q.isPending} error={q.error}>{q.data && <dl className="co-bg-white co-border co-border-[#dce3e6] co-rounded co-p-5 co-grid co-gap-3"><div><dt>Aplicación</dt><dd>{q.data.application === 'ok' ? 'Disponible' : 'No disponible'}</dd></div><div><dt>Base de datos</dt><dd>{q.data.database === 'ok' ? 'Disponible' : 'No disponible'}</dd></div><div><dt>Modelo de IA</dt><dd>No comprobado en esta consulta</dd></div></dl>}</Load></>;
}
