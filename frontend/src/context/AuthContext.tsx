/**
 * Auth context for plan tier (Simple vs Pro).
 * user.plan is set by login response / JWT claim; until then we use a default (e.g. from localStorage).
 */
import { createContext, useContext, useState, useMemo, type ReactNode } from 'react';

export type UserPlan = 'simple' | 'pro';

export interface AuthUser {
  plan: UserPlan;
}

interface AuthContextValue {
  user: AuthUser | null;
  setUser: (user: AuthUser | null) => void;
}

const STORAGE_KEY = 'noctua_user_plan';

function getStoredPlan(): UserPlan {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === 'pro' || v === 'simple') return v;
  } catch {
    /* ignore */
  }
  return 'simple';
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(() => ({ plan: getStoredPlan() }));

  const setUser = useMemo(() => {
    return (u: AuthUser | null) => {
      setUserState(u);
      if (u?.plan) {
        try {
          localStorage.setItem(STORAGE_KEY, u.plan);
        } catch {
          /* ignore */
        }
      }
    };
  }, []);

  const value = useMemo(() => ({ user, setUser }), [user, setUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}
