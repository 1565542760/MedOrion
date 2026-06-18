'use client';

import Link from 'next/link';
import { Card, Space, Typography } from 'antd';

export default function Page() {
  return (
    <main style={{ padding: 24, width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <Space direction='vertical' size={4}>
          <Typography.Title level={3} style={{ margin: 0 }}>溯源</Typography.Title>
          <Typography.Text type='secondary'>溯源视图以病例上下文为准，不占主导航主位。</Typography.Text>
        </Space>
        <Card title='入口说明'>
          <Space direction='vertical' size={8}>
            <Typography.Text>请先进入具体病例，在病例页内查看 trace、evidence 和血缘链。</Typography.Text>
            <Link href='/cases'>去患者/病例列表</Link>
          </Space>
        </Card>
      </Space>
    </main>
  );
}
