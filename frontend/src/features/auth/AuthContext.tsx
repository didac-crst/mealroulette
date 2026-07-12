import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import * as authApi from "../../api/auth";
import type { UserPublic } from "../../api/auth";
import { ApiError } from "../../api/client";
import { clearTokens, loadTokens, saveTokens } from "./authStorage";

type AuthContextValue = {
  user: UserPublic | null;
  accessToken: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAdmin: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const SESSION_RESTORE_ATTEMPTS = 5;
const SESSION_RESTORE_DELAY_MS = 1_000;

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function fetchMeWithRetry(accessToken: string): Promise<UserPublic> {
  let lastError: unknown;
  for (let attempt = 0; attempt < SESSION_RESTORE_ATTEMPTS; attempt += 1) {
    try {
      return await authApi.fetchMe(accessToken);
    } catch (error) {
      lastError = error;
      if (error instanceof ApiError && error.status === 401) {
        throw error;
      }
      if (attempt < SESSION_RESTORE_ATTEMPTS - 1) {
        await sleep(SESSION_RESTORE_DELAY_MS * (attempt + 1));
      }
    }
  }
  throw lastError;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const applySession = useCallback((token: string, me: UserPublic) => {
    setAccessToken(token);
    setUser(me);
  }, []);

  const clearSession = useCallback(() => {
    clearTokens();
    setAccessToken(null);
    setUser(null);
  }, []);

  const restoreSession = useCallback(async () => {
    const stored = loadTokens();
    if (!stored) {
      setLoading(false);
      return;
    }

    try {
      const me = await fetchMeWithRetry(stored.accessToken);
      applySession(stored.accessToken, me);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        try {
          const tokens = await authApi.refresh(stored.refreshToken);
          saveTokens({
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
          });
          const me = await fetchMeWithRetry(tokens.access_token);
          applySession(tokens.access_token, me);
          setLoading(false);
          return;
        } catch {
          clearSession();
        }
      } else {
        // Keep stored tokens on transient errors; session restore can retry on reload.
      }
    } finally {
      setLoading(false);
    }
  }, [applySession, clearSession]);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  const login = useCallback(
    async (username: string, password: string) => {
      const tokens = await authApi.login(username, password);
      saveTokens({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });
      const me = await fetchMeWithRetry(tokens.access_token);
      applySession(tokens.access_token, me);
    },
    [applySession],
  );

  const logout = useCallback(async () => {
    const stored = loadTokens();
    if (stored) {
      try {
        await authApi.logout(stored.refreshToken);
      } catch {
        // still clear local session
      }
    }
    clearSession();
  }, [clearSession]);

  const value = useMemo(
    () => ({
      user,
      accessToken,
      loading,
      login,
      logout,
      isAdmin: user?.role === "admin",
    }),
    [user, accessToken, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
