'use client';

import { use } from 'react';
import { Card, Space, Typography } from 'antd';
import LineagePlaceholder from '@/components/LineagePlaceholder';

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return <Space direction='vertical' size={16} style={{ width: '100%' }}><Typography.Title level={4} style={{ margin: 0 }}>数据血缘与错误溯源</Typography.Title><Typography.Text type='secondary'>病例：{caseId}</Typography.Text><Card title='血缘图占位'><LineagePlaceholder /></Card></Space>;
}
