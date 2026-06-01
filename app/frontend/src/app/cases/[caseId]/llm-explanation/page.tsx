'use client';

import { use, useEffect, useState } from 'react';
import { Card, Space, Tag, Typography } from 'antd';
import { getRecommendations } from '@/lib/api';

type RecommendationRow = { recommendation_id: string; title: string; trace_id?: string };

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [rows, setRows] = useState<RecommendationRow[]>([]);

  useEffect(() => {
    getRecommendations(caseId, 'trace-demo').then((data) => setRows(Array.isArray(data) ? data as RecommendationRow[] : [])).catch(() => setRows([]));
  }, [caseId]);

  return <Space direction='vertical' size={16} style={{ width: '100%' }}><Typography.Title level={4} style={{ margin: 0 }}>大模型解释与医生问答</Typography.Title><Typography.Text type='secondary'>Case: {caseId}</Typography.Text><Card title='解释结果占位'><Typography.Paragraph>展示引用的小模型、输入数据与知识库证据链。</Typography.Paragraph><Space wrap>{rows.map((item) => <Tag key={item.recommendation_id}>{item.title} (trace: {item.trace_id})</Tag>)}</Space></Card></Space>;
}
