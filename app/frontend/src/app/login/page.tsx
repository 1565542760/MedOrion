'use client';

import { useEffect, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser, login as apiLogin } from '@/lib/api';

type ApiError = {
  response?: {
    data?: {
      detail?: {
        code?: string;
      };
    };
  };
};

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    void getCurrentUser()
      .then(() => {
        if (!active) return;
        router.replace('/dashboard');
      })
      .catch(() => {
        if (!active) return;
        setReady(true);
      });

    return () => {
      active = false;
    };
  }, [router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await apiLogin(username.trim(), password);
      router.replace('/dashboard');
    } catch (e: unknown) {
      const code = (e as ApiError)?.response?.data?.detail?.code;
      if (code === 'invalid_credentials') {
        setError('用户名或密码错误，请重试。');
      } else if (code === 'auth_storage_not_ready') {
        setError('本地认证存储尚未就绪，请刷新后重试。');
      } else {
        setError('登录失败，请稍后重试。');
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (!ready) {
    return (
      <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: '#f3f6fb', color: '#334155' }}>
        <div style={{ fontSize: 14 }}>正在检查登录状态...</div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24, background: '#f3f6fb' }}>
      <section style={{ width: '100%', maxWidth: 440, background: '#fff', borderRadius: 16, boxShadow: '0 12px 40px rgba(15, 23, 42, 0.12)', padding: 28, border: '1px solid #e5e7eb' }}>
        <form onSubmit={onSubmit} style={{ display: 'grid', gap: 16 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, lineHeight: 1.3, color: '#0f172a' }}>登录</h1>
            <p style={{ margin: '8px 0 0', color: '#64748b', fontSize: 14 }}>开发环境最小登录入口（非生产公网登录）。</p>
          </div>

          {error ? (
            <div style={{ border: '1px solid #fecaca', background: '#fef2f2', color: '#991b1b', borderRadius: 10, padding: '10px 12px', fontSize: 14 }}>
              {error}
            </div>
          ) : null}

          <label style={{ display: 'grid', gap: 8, fontSize: 14, color: '#0f172a' }}>
            <span>用户名</span>
            <input
              autoComplete='username'
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder='请输入用户名'
              style={{ height: 42, borderRadius: 10, border: '1px solid #cbd5e1', padding: '0 12px', fontSize: 14, color: '#0f172a', background: '#fff', outline: 'none' }}
            />
          </label>

          <label style={{ display: 'grid', gap: 8, fontSize: 14, color: '#0f172a' }}>
            <span>密码</span>
            <input
              autoComplete='current-password'
              type='password'
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder='请输入密码'
              style={{ height: 42, borderRadius: 10, border: '1px solid #cbd5e1', padding: '0 12px', fontSize: 14, color: '#0f172a', background: '#fff', outline: 'none' }}
            />
          </label>

          <button
            type='submit'
            disabled={submitting}
            style={{
              height: 44,
              border: 'none',
              borderRadius: 10,
              background: submitting ? '#93c5fd' : '#2563eb',
              color: '#fff',
              fontSize: 15,
              fontWeight: 600,
              cursor: submitting ? 'not-allowed' : 'pointer'
            }}
          >
            {submitting ? '正在登录...' : '登录'}
          </button>
        </form>
      </section>
    </main>
  );
}
