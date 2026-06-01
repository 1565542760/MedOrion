'use client';
import '@ant-design/v5-patch-for-react-19';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Layout, Menu, Space, Tag, Typography } from 'antd';
import { apiConfig } from '@/lib/api';

const { Header, Sider, Content } = Layout;

const items = [
  { key: '/dashboard', label: <Link href='/dashboard'>工作台总览</Link> },
  { key: '/cases', label: <Link href='/cases'>病例列表</Link> },
  { key: '/models', label: <Link href='/models'>模型管理</Link> },
  { key: '/learning-library', label: <Link href='/learning-library'>持续学习病例库</Link> }
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const selected = items.find((x) => pathname.startsWith(x.key))?.key || '/dashboard';

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
          <Space>
            <Tag color='blue'>Stage 01</Tag>
            <Tag color='geekblue'>API: {apiConfig.mode}</Tag>
            <Tag>Base URL: {apiConfig.baseURL}</Tag>
          </Space>
        </Header>
        <Content style={{ padding: 20 }}>{children}</Content>
      </Layout>
    </Layout>
  );
}
