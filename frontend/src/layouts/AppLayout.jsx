import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  async function handleLogout() { await logout(); navigate('/login', { replace: true }) }
  return <div className="app-shell">
    <nav className="navbar navbar-expand-lg navbar-dark dental-navbar">
      <div className="container">
        <NavLink className="navbar-brand" to="/"><i className="bi bi-heart-pulse-fill me-2" />SmileManager</NavLink>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav" aria-controls="mainNav" aria-expanded="false" aria-label="Abrir navegación"><span className="navbar-toggler-icon" /></button>
        <div className="collapse navbar-collapse" id="mainNav">
          <div className="navbar-nav me-auto">
            <NavLink className="nav-link" to="/"><i className="bi bi-house-door me-1" /> Inicio</NavLink>
            <NavLink className="nav-link" to="/appointments"><i className="bi bi-calendar3 me-1" /> Citas</NavLink>
            <NavLink className="nav-link" to="/patients"><i className="bi bi-people me-1" /> Pacientes</NavLink>
            <NavLink className="nav-link" to="/diagnostics"><i className="bi bi-card-image me-1" /> Diagnósticos</NavLink>
          </div>
          <span className="navbar-text text-white me-3"><i className="bi bi-person-circle me-1" />{user.username}</span>
          <button className="btn btn-sm btn-outline-light" onClick={handleLogout}><i className="bi bi-box-arrow-right me-1" />Salir</button>
        </div>
      </div>
    </nav>
    <main><Outlet /></main>
    <footer className="bg-white border-top py-4 mt-auto"><div className="container d-flex justify-content-between"><span>SmileManager</span><NavLink to="/privacy">Aviso de Privacidad</NavLink></div></footer>
  </div>
}
