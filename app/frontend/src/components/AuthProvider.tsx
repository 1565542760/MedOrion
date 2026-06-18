'use client';

import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  CurrentUser,
  clearAuthTokens,
  getCurrentUser,
  login as apiLogin,
  logout as apiLogout,
  refreshToken as apiRefreshToken,
} from '@/lib/api';

type AuthContextValue = {
  loading: boolean;
  hydrated: boolean;
  isAuthenticated: boolean;
  currentUser: CurrentUser | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  reloadCurrentUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const protectedPrefixes = ['/dashboard', '/cases', '/model-workflow', '/audit', '/quality-reviews', '/models', '/settings', '/feedback', '/lineage'];
const DEV_AUTO_LOGIN_USERNAME = process.env.NEXT_PUBLIC_DEV_AUTO_LOGIN_USERNAME || 'dev_doctor';
const DEV_AUTO_LOGIN_PASSWORD = process.env.NEXT_PUBLIC_DEV_AUTO_LOGIN_PASSWORD || '123456';

function isProtectedPath(pathname: string) {
  return protectedPrefixes.some((prefix) => pathname.startsWith(prefix));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const attemptedDevAutoLoginRef = useRef(false);
  const [hydrated, setHydrated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    let active = true;

    const bootstrapAuth = async () => {
      setLoading(true);
      try {
        const user = await getCurrentUser();
        if (!active) return;
        setCurrentUser(user);
        return;
      } catch {
        if (!active) return;
        try {
          await apiRefreshToken();
          const user = await getCurrentUser();
          if (!active) return;
          setCurrentUser(user);
          return;
        } catch {
          if (!active) return;
          const shouldAutoLogin = pathname !== '/login'
            && isProtectedPath(pathname)
            && !attemptedDevAutoLoginRef.current;

          if (shouldAutoLogin) {
            attemptedDevAutoLoginRef.current = true;
            try {
              await apiLogin(DEV_AUTO_LOGIN_USERNAME, DEV_AUTO_LOGIN_PASSWORD);
              const user = await getCurrentUser();
              if (!active) return;
              setCurrentUser(user);
              return;
            } catch {
              clearAuthTokens();
            }
          } else {
            clearAuthTokens();
          }

          if (!active) return;
          setCurrentUser(null);
        }
      } finally {
        if (!active) return;
        setHydrated(true);
        setLoading(false);
      }
    };

    void bootstrapAuth();

    return () => {
      active = false;
    };
  }, [pathname]);

  useEffect(() => {
    if (!hydrated || loading) return;
    const protectedPath = isProtectedPath(pathname);
    if (!currentUser && protectedPath && pathname !== '/login') {
      router.replace('/login');
      return;
    }
    if (currentUser && pathname === '/login') {
      router.replace('/dashboard');
    }
  }, [hydrated, loading, currentUser, pathname, router]);

  const value = useMemo<AuthContextValue>(() => ({
    loading,
    hydrated,
    isAuthenticated: !!currentUser,
    currentUser,
    login: async (username: string, password: string) => {
      await apiLogin(username, password);
      const user = await getCurrentUser();
      setCurrentUser(user);
      setHydrated(true);
      setLoading(false);
    },
    logout: async () => {
      await apiLogout();
      setCurrentUser(null);
      setHydrated(true);
      setLoading(false);
    },
    reloadCurrentUser: async () => {
      const user = await getCurrentUser();
      setCurrentUser(user);
      setHydrated(true);
      setLoading(false);
    },
  }), [hydrated, loading, currentUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return ctx;
}
