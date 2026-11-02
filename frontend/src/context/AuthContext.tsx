import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api, setAccessToken, waitForAuthRefresh } from "../api/client";
import type { SessionResponse, SessionUser } from "../types/domain";
import { queryClient } from "../query/client";

interface AuthValue {
  user: SessionUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);

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
    const expire = () => { setAccessToken(null); queryClient.clear(); setUser(null); };
    window.addEventListener("smile:auth-expired", expire);
    return () => window.removeEventListener("smile:auth-expired", expire);
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const result = await api<{ access: string; user: SessionUser }>("auth/login/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      queryClient.clear();
      setAccessToken(result.access);
      setUser(result.user);
    },
    [],
  );

  const logout = useCallback(async () => {
    await waitForAuthRefresh();
    await api("auth/logout/", { method: "POST" });
    setAccessToken(null);
    queryClient.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("AuthProvider no está disponible.");
  return context;
}
