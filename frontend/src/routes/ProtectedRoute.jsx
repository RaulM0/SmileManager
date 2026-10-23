import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="page-loader"><div className="spinner-border text-primary" /></div>
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}
