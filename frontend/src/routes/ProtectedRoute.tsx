import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading)
    return (
      <div className="page-loader" role="status" aria-label="Comprobando sesión">
        <div className="workspace-loader-spinner" />
      </div>
    );
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  return <Outlet />;
}
