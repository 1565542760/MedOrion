'use client';
import '@ant-design/v5-patch-for-react-19';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Button, Layout, Menu, Space, Tag, Typography } from 'antd';
import { apiConfig } from '@/lib/api';
import { useAuth } from '@/components/AuthProvider';

const { Header, Sider, Content } = Layout;

const items = [
  { key: '/dashboard', label: <Link href='/dashboard'>工作台总览</Link> },
  { key: '/cases', label: <Link href='/cases'>病例列表</Link> },
  { key: '/models', label: <Link href='/models'>模型管理</Link> },
  { key: '/learning-library', label: <Link href='/learning-library'>持续学习病例库</Link> }
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { currentUser, isAuthenticated, logout } = useAuth();

  if (pathname === '/login') {
    return <>{children}</>;
  }

  const selected = items.find((x) => pathname.startsWith(x.key))?.key || '/dashboard';

  async function handleLogout() {
    await logout();
    router.replace('/login');
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme='light' width={230}>
        <div style={{ padding: 14, borderBottom: '1px solid #f0f0f0' }}>
          <Typography.Title level={5} style={{ margin: 0 }}>MedOrion 医生工作台</Typography.Title>
        </div>
        <Menu mode='inline' selectedKeys={[selected]} items={items} style={{ borderInlineEnd: 0 }} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', paddingInline: 20, borderBottom: '1px solid #f0f0f0' }}>
          <Space wrap>
            <Tag color='blue'>开发环境</Tag>
            <Tag color='geekblue'>API: {apiConfig.mode}</Tag>
            <Tag>Base URL: {apiConfig.baseURL}</Tag>
            {isAuthenticated ? <Tag color='green'>当前用户：{currentUser?.display_name || currentUser?.username || '-'}</Tag> : null}
            {isAuthenticated ? <Tag>角色：{currentUser?.role || '-'}</Tag> : null}
            {isAuthenticated ? <Button onClick={handleLogout}>退出登录</Button> : null}
          </Space>
        </Header>
        <Content style={{ padding: 20 }}>{children}</Content>
      </Layout>
    </Layout>
  );
}
