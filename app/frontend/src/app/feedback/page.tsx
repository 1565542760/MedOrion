'use client';

import Link from 'next/link';
import { Card, Space, Typography } from 'antd';

export default function Page() {
  return (
    <main style={{ padding: 24, width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <Space direction='vertical' size={4}>
          <Typography.Title level={3} style={{ margin: 0 }}>医生反馈</Typography.Title>
          <Typography.Text type='secondary'>反馈功能收敛到病例内操作，不再作为主导航入口。</Typography.Text>
        </Space>
        <Card title='入口说明'>
          <Space direction='vertical' size={8}>
            <Typography.Text>请先进入具体病例，在病例页内提交反馈、查看 trace 和推荐关联。</Typography.Text>
            <Link href='/cases'>去患者/病例列表</Link>
          </Space>
        </Card>
      </Space>
    </main>
  );
}
