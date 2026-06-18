'use client';
import '@ant-design/v5-patch-for-react-19';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Button, Layout, Menu, Space, Tag, Typography } from 'antd';
import { apiConfig } from '@/lib/api';
import { useAuth } from '@/components/AuthProvider';

const { Header, Sider, Content } = Layout;

const items = [
  { key: '/dashboard', label: <Link href='/dashboard'>工作台</Link> },
  { key: '/cases', label: <Link href='/cases'>患者/病例</Link> },
  { key: '/model-workflow', label: <Link href='/model-workflow'>模型评估</Link> },
  { key: '/audit', label: <Link href='/audit'>审计</Link> },
  { key: '/quality-reviews', label: <Link href='/quality-reviews'>质控</Link> },
  { key: '/models', label: <Link href='/models'>模型管理</Link> },
  { key: '/settings', label: <Link href='/settings'>设置</Link> },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { currentUser, isAuthenticated, logout, hydrated } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setMounted(true), 0);
    return () => window.clearTimeout(timer);
  }, []);

  if (pathname === '/login') return <>{children}</>;

  const selected = items.find((item) => pathname.startsWith(item.key))?.key || '/dashboard';

  async function handleLogout() {
    await logout();
    router.replace('/login');
  }

  const authReady = mounted && hydrated;
  const authUserLabel = authReady
    ? (isAuthenticated ? (currentUser?.display_name || currentUser?.username || '-') : '未登录')
    : '认证中';
  const authRoleLabel = authReady
    ? (isAuthenticated ? (currentUser?.role || '-') : '待登录')
    : '认证中';

  return (
    <Layout style={{ minHeight: '100vh', overflowX: 'hidden', background: '#f5f7fb' }}>
      <Sider theme='light' width={220} style={{ borderRight: '1px solid #eef0f4' }}>
        <div style={{ padding: 16, borderBottom: '1px solid #eef0f4' }}>
          <Typography.Title level={5} style={{ margin: 0 }}>MedOrion</Typography.Title>
          <Typography.Text type='secondary' style={{ fontSize: 12 }}>院内医生工作站</Typography.Text>
        </div>
        <Menu mode='inline' selectedKeys={[selected]} items={items} style={{ borderInlineEnd: 0, paddingTop: 8 }} />
      </Sider>
      <Layout style={{ minWidth: 0 }}>
        <Header style={{ background: '#fff', paddingInline: 20, borderBottom: '1px solid #eef0f4', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
          <Space wrap size={8}>
            <Tag color='blue'>API：{apiConfig.mode}</Tag>
            <Tag color='gold'>科研与辅助评估，不作为临床诊断依据</Tag>
          </Space>
          <Space wrap size={8}>
            <Tag color={authReady && isAuthenticated ? 'green' : 'default'}>{authUserLabel}</Tag>
            <Tag color={authReady && isAuthenticated ? undefined : 'default'}>{authRoleLabel}</Tag>
            {authReady && isAuthenticated ? <Button size='small' onClick={handleLogout}>退出</Button> : null}
          </Space>
        </Header>
        <Content style={{ padding: 20, minWidth: 0, overflowX: 'hidden' }}>{children}</Content>
      </Layout>
    </Layout>
  );
}
