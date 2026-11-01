import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { api, setCsrfToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshSession = useCallback(async () => {
    const session = await api("auth/session/");
    setCsrfToken(session.csrf_token);
    setUser(session.authenticated ? session.user : null);
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

  const login = useCallback(
    async (username, password) => {
      await refreshSession();
      const result = await api("auth/login/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      setCsrfToken(result.csrf_token);
      setUser(result.user);
    },
    [refreshSession],
  );

  const logout = useCallback(async () => {
    await api("auth/logout/", { method: "POST" });
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
  return useContext(AuthContext);
}
