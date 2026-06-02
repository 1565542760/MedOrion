'use client';

import Link from 'next/link';
import { use, useMemo } from 'react';
import { Card, Space, Tag, Typography } from 'antd';
import { useSearchParams } from 'next/navigation';
import LineagePlaceholder from '@/components/LineagePlaceholder';

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const searchParams = useSearchParams();
  const traceId = searchParams.get('trace_id') || '';
  const traceHref = useMemo(() => traceId ? ('/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(traceId)) : ('/cases/' + caseId + '/lineage'), [caseId, traceId]);

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>数据血缘与错误溯源</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}</Typography.Text>
      {traceId ? <Tag color='blue'>trace_id: {traceId} <Link href={traceHref}>刷新当前溯源</Link></Tag> : null}
      <Card title='血缘图占位'><LineagePlaceholder /></Card>
    </Space>
  );
}
