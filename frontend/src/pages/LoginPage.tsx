import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { api, getErrorMessage } from "../api/client";
import type { LoginResult } from '../types/domain';

export default function LoginPage() {
  const { user, loading, login, completeLogin } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({ username: "", password: "" });
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [challenge, setChallenge] = useState('');
  const [setupSecret, setSetupSecret] = useState('');
  const [code, setCode] = useState('');
  const [recoveryResult, setRecoveryResult] = useState<LoginResult | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const requestedLocation = location.state?.from;
  const returnTo = requestedLocation
    ? `${requestedLocation.pathname}${requestedLocation.search || ""}${requestedLocation.hash || ""}`
    : "/";
  if (!loading && user) return <Navigate to={returnTo} replace />;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    try {
      if (challenge) {
        const result = await api<LoginResult>('auth/mfa/verify/', { method: 'POST', body: JSON.stringify({ challenge, code }) });
        setCode('');
        setSetupSecret('');
        if (result.recovery_codes?.length) { setRecoveryResult(result); return; }
        completeLogin(result);
      } else {
        const result = await login(form.username, form.password);
        setForm((previous) => ({ ...previous, password: '' }));
        if (result.mfa_required && result.challenge) {
          setChallenge(result.challenge);
          if (result.enrollment_required) {
            const setup = await api<{ secret: string }>('auth/mfa/setup/', { method: 'POST', body: JSON.stringify({ challenge: result.challenge }) });
            setSetupSecret(setup.secret);
          }
          return;
        }
      }
      toast.success("Sesión iniciada.");
      navigate(returnTo, { replace: true });
    } catch (requestError) {
      toast.error(getErrorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <div className="login-workspace">
      <div className="login-shell">
        <section className="login-context" aria-label="SmileManager">
          <div className="login-brand"><span className="login-brand-mark"><i className="bi bi-heart-pulse" aria-hidden="true" /></span><strong>SmileManager</strong></div>
          <div className="login-context-copy">
            <h1>Espacio de trabajo clínico</h1>
            <p>Sistema de gestión odontológica integral</p>
            <ul>
              <li><i className="bi bi-graph-up" aria-hidden="true" />Análisis con inteligencia artificial</li>
              <li><i className="bi bi-database-check" aria-hidden="true" />Historiales clínicos seguros</li>
              <li><i className="bi bi-calendar2-check" aria-hidden="true" />Gestión de citas integrada</li>
            </ul>
          </div>
        </section>
        <main className="login-form-panel">
          <div className="login-form-inner">
            <h2>Bienvenido de nuevo</h2>
            <p>Ingrese sus credenciales para acceder al sistema</p>
            {requestedLocation?.pathname === "/invitations/accept" && requestedLocation.hash &&
              <p>¿Aún no tienes cuenta? <Link to={{ pathname: "/invitations/register", hash: requestedLocation.hash }}>Crear cuenta con la invitación</Link></p>}
            {recoveryResult ? <section aria-label="Códigos de recuperación">
              <h3>Guarda tus códigos de recuperación</h3><p>Cada código permite un solo uso junto con tu contraseña. Se muestran una sola vez; consérvalos en un lugar privado.</p>
              <ul>{recoveryResult.recovery_codes?.map((value) => <li key={value}><code>{value}</code></li>)}</ul>
              <button className="clinical-form-submit" onClick={() => { completeLogin(recoveryResult); setRecoveryResult(null); navigate(returnTo, { replace: true }); }}>He guardado los códigos</button>
            </section> : <form onSubmit={submit}>
              {challenge ? <section aria-label="Segundo factor">
                <h3>{setupSecret ? 'Configura tu autenticador' : 'Verifica tu identidad'}</h3>
                {setupSecret && <><p>Agrega una cuenta TOTP en tu aplicación autenticadora con esta clave. El código cambia cada 30 segundos.</p><code aria-label="Clave del autenticador">{setupSecret}</code></>}
                <label className="clinical-form-label" htmlFor="mfa-code">Código del autenticador o de recuperación</label>
                <input id="mfa-code" className="clinical-form-control" autoComplete="one-time-code" required value={code} maxLength={128} onChange={(event) => setCode(event.target.value)} />
                <p>Si el código ya fue utilizado, espera al siguiente. La verificación vence en cinco minutos.</p>
                <button className="clinical-form-submit" disabled={submitting}>{submitting ? 'Verificando…' : 'Verificar'}</button>
                <button type="button" disabled={submitting} onClick={() => { setChallenge(''); setSetupSecret(''); setCode(''); }}>Volver al inicio de sesión</button>
              </section> : <>
              <div className="clinical-form-field">
                <label className="clinical-form-label" htmlFor="username">Usuario</label>
                <input
                  id="username"
                  autoComplete="username"
                  className="clinical-form-control"
                  required
                  placeholder="Ingrese su nombre de usuario"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                />
              </div>
              <div className="clinical-form-field">
                <label className="clinical-form-label" htmlFor="password">Contraseña</label>
                <div className="login-password-field">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    className="clinical-form-control"
                    required
                    placeholder="Ingrese su contraseña"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                  />
                  <button
                    type="button"
                    className="login-password-toggle"
                    aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                    aria-pressed={showPassword}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    <i className={`bi bi-eye${showPassword ? "-slash" : ""}`} aria-hidden="true" />
                  </button>
                </div>
              </div>
              <p className="co-mt-3"><Link to="/forgot-password">¿Olvidaste tu contraseña?</Link></p>
              <button disabled={submitting} className="clinical-form-submit co-mt-5 co-w-full">
                {submitting ? <><span className="clinical-form-spinner" aria-hidden="true" />Iniciando sesión…</> : <><i className="bi bi-box-arrow-in-right" aria-hidden="true" />Iniciar sesión</>}
              </button>
              </>}
            </form>}
          </div>
        </main>
      </div>
      <p className="login-security-note"><i className="bi bi-shield-check" aria-hidden="true" />Información clínica · Acceso exclusivo de personal autorizado</p>
    </div>
  );
}
