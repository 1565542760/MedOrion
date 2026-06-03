'use client';

import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Spin } from 'antd';
import {
  CurrentUser,
  clearAuthTokens,
  getCurrentUser,
  login as apiLogin,
  logout as apiLogout,
  readCurrentUser,
  refreshToken as apiRefreshToken,
} from '@/lib/api';

type AuthContextValue = {
  loading: boolean;
  isAuthenticated: boolean;
  currentUser: CurrentUser | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  reloadCurrentUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const protectedPrefixes = ['/dashboard', '/cases', '/models', '/learning-library', '/feedback', '/quality-reviews', '/lineage'];

function isProtectedPath(pathname: string) {
  return protectedPrefixes.some((prefix) => pathname.startsWith(prefix));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(() => readCurrentUser());

  useEffect(() => {
    getCurrentUser()
      .then((user) => {
        setCurrentUser(user);
      })
      .catch(async () => {
        try {
          await apiRefreshToken();
          const user = await getCurrentUser();
          setCurrentUser(user);
        } catch {
          clearAuthTokens();
          setCurrentUser(null);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (loading) return;
    const protectedPath = isProtectedPath(pathname);
    if (!currentUser && protectedPath) {
      router.replace('/login');
      return;
    }
    if (currentUser && pathname === '/login') {
      router.replace('/dashboard');
    }
  }, [loading, currentUser, pathname, router]);

  const value = useMemo<AuthContextValue>(() => ({
    loading,
    isAuthenticated: !!currentUser,
    currentUser,
    login: async (username: string, password: string) => {
      await apiLogin(username, password);
      const user = await getCurrentUser();
      setCurrentUser(user);
    },
    logout: async () => {
      await apiLogout();
      setCurrentUser(null);
    },
    reloadCurrentUser: async () => {
      const user = await getCurrentUser();
      setCurrentUser(user);
    },
  }), [loading, currentUser]);

  if (loading && isProtectedPath(pathname)) {
    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24 }}>
        <Spin spinning tip='正在检查登录状态...'>
          <div style={{ width: 320, height: 80 }} />
        </Spin>
      </div>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return ctx;
}
