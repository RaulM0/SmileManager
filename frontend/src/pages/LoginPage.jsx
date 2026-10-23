import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  if (!loading && user) return <Navigate to="/" replace />;
  async function submit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(form.username, form.password);
      navigate(location.state?.from?.pathname || "/", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <div className="login-container">
      <div className="container py-5">
        <div className="row justify-content-center">
          <div className="col-md-10 col-lg-8">
            <div className="card login-card shadow-lg border-0">
              <div className="row g-0">
                <div className="col-md-6 login-left-panel">
                  <div>
                    <div className="dental-icon">
                      <i className="bi bi-shield-shaded" />
                    </div>
                    <h1>
                      SmileManager <span>Pro</span>
                    </h1>
                    <p>Sistema de gestión odontológica integral</p>
                    <div className="features-list">
                      <div>
                        <i className="bi bi-graph-up" /> Análisis con
                        inteligencia artificial
                      </div>
                      <div>
                        <i className="bi bi-database-check" /> Historiales
                        clínicos seguros
                      </div>
                      <div>
                        <i className="bi bi-calendar2-check" /> Gestión de citas
                        integrada
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="card-body p-5">
                    <h2>Bienvenido de nuevo</h2>
                    <p className="text-muted">
                      Ingrese sus credenciales para acceder al sistema
                    </p>
                    <form onSubmit={submit}>
                      <label className="form-label" htmlFor="username">
                        Usuario
                      </label>
                      <div className="input-group mb-3">
                        <span className="input-group-text">
                          <i className="bi bi-person-circle" />
                        </span>
                        <input
                          id="username"
                          className="form-control"
                          required
                          placeholder="Ingrese su nombre de usuario"
                          value={form.username}
                          onChange={(e) =>
                            setForm({ ...form, username: e.target.value })
                          }
                        />
                      </div>
                      <label className="form-label" htmlFor="password">
                        Contraseña
                      </label>
                      <div className="input-group mb-4">
                        <span className="input-group-text">
                          <i className="bi bi-key" />
                        </span>
                        <input
                          id="password"
                          type={showPassword ? "text" : "password"}
                          className="form-control"
                          required
                          placeholder="Ingrese su contraseña"
                          value={form.password}
                          onChange={(e) =>
                            setForm({ ...form, password: e.target.value })
                          }
                        />
                        <button
                          type="button"
                          className="input-group-text"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          <i
                            className={`bi bi-eye${showPassword ? "-slash" : ""}`}
                          />
                        </button>
                      </div>
                      <button
                        disabled={submitting}
                        className="btn btn-primary w-100"
                      >
                        {submitting ? (
                          <span className="spinner-border spinner-border-sm" />
                        ) : (
                          <>
                            <i className="bi bi-box-arrow-in-right me-2" />
                            Iniciar sesión
                          </>
                        )}
                      </button>
                      {error && (
                        <div className="alert alert-danger mt-3">
                          <i className="bi bi-exclamation-circle me-2" />
                          {error}
                        </div>
                      )}
                    </form>
                  </div>
                </div>
              </div>
            </div>
            <div className="text-center text-muted mt-4">
              <i className="bi bi-shield-check me-2" />
              Sistema seguro · Protegido con encriptación
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
