'use client';

import { use } from 'react';
import { Card, Space, Typography } from 'antd';

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return <Space direction='vertical' size={16} style={{ width: '100%' }}><Typography.Title level={4} style={{ margin: 0 }}>患者动态病情反馈（预留）</Typography.Title><Typography.Text type='secondary'>病例：{caseId}</Typography.Text><Card>预留未来接入可穿戴设备流数据。</Card></Space>;
}
