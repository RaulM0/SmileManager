import { useToast } from "./ToastContext";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api, getErrorMessage, setAccessToken, waitForAuthRefresh } from "../api/client";
import { ConfirmDialog } from '../components/ConfirmDialog';
import type { LoginResult, SessionResponse, SessionUser } from "../types/domain";
import { queryClient } from "../query/client";

interface AuthValue {
  user: SessionUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<LoginResult>;
  completeLogin: (result: LoginResult) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const toast = useToast();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [reauth, setReauth] = useState(false);
  const [reauthForm, setReauthForm] = useState({ password: '', code: '' });
  const [reauthError, setReauthError] = useState('');
  const [reauthBusy, setReauthBusy] = useState(false);
  useEffect(() => {
    const open = () => { setReauthError(''); setReauth(true); };
    window.addEventListener('smile:reauth-required', open);
    return () => window.removeEventListener('smile:reauth-required', open);
  }, []);
  const completeLogin = useCallback((result: LoginResult) => {
    if (!result.access || !result.user) throw new Error('Respuesta de autenticación incompleta.');
    queryClient.clear();
    setAccessToken(result.access);
    setUser(result.user);
  }, []);

  const refreshSession = useCallback(async () => {
    const session = await api<SessionResponse>("auth/session/");
    setAccessToken(session.access ?? null);
    setUser(session.authenticated ? session.user ?? null : null);
    setLoading(false);
    return session;
  }, []);

  useEffect(() => {
    async function initializeSession() {
      try {
        await refreshSession();
      } catch {
        setLoading(false);
      }
    }
    initializeSession();
  }, [refreshSession]);

  useEffect(() => {
    const expire = () => { setAccessToken(null); queryClient.clear(); setUser(null); setReauth(false); setReauthForm({ password: '', code: '' }); };
    window.addEventListener("smile:auth-expired", expire);
    return () => window.removeEventListener("smile:auth-expired", expire);
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const result = await api<LoginResult>("auth/login/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      if (result.authenticated) completeLogin(result);
      return result;
    },
    [completeLogin],
  );

  const logout = useCallback(async () => {
    await waitForAuthRefresh();
    await api("auth/logout/", { method: "POST" });
    setAccessToken(null);
    queryClient.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, completeLogin, logout }),
    [user, loading, login, completeLogin, logout],
  );
  async function confirmIdentity() {
    if (reauthBusy) return;
    if (!reauthForm.password) { setReauthError('Ingresa tu contraseña.'); toast.warning('Ingresa tu contraseña.'); return; }
    setReauthBusy(true);
    try {
      await api('auth/reauthenticate/', { method: 'POST', body: JSON.stringify(reauthForm) });
      toast.success('Identidad confirmada. Vuelve a enviar la operación.');
      setReauth(false);
      setReauthForm({ password: '', code: '' });
      setReauthError('');
    } catch (error) { setReauthError(getErrorMessage(error)); toast.error(getErrorMessage(error)); }
    finally { setReauthBusy(false); }
  }
  return <AuthContext.Provider value={value}>{children}
    {reauth && user && <ConfirmDialog title="Confirma tu identidad" confirmLabel="Confirmar identidad" variant="primary" busyLabel="Verificando…" busy={reauthBusy} onConfirm={() => void confirmIdentity()} onClose={() => { setReauth(false); setReauthForm({ password: '', code: '' }); }}>
      <div className="reauth-dialog-body"><p className="reauth-dialog-description">Ingresa tu contraseña para continuar. Después de confirmar, vuelve a enviar la operación que estabas realizando.</p>
      <div className="clinical-form-field"><label className="clinical-form-label" htmlFor="reauth-password">Contraseña</label><input id="reauth-password" className="clinical-form-control" type="password" autoComplete="current-password" value={reauthForm.password} onChange={(event) => setReauthForm({ ...reauthForm, password: event.target.value })} /></div>
      {user.mfa_enabled && <div className="clinical-form-field"><label className="clinical-form-label" htmlFor="reauth-code">Código del autenticador o de recuperación</label><input id="reauth-code" className="clinical-form-control" autoComplete="one-time-code" value={reauthForm.code} onChange={(event) => setReauthForm({ ...reauthForm, code: event.target.value })} /></div>}
      {reauthError && <p className="clinical-form-alert" role="alert">{reauthError}</p>}</div>
    </ConfirmDialog>}
  </AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("AuthProvider no está disponible.");
  return context;
}
