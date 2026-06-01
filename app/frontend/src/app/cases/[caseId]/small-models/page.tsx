'use client';

import { use } from 'react';
import { Card, Space, Statistic, Typography } from 'antd';

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return <Space direction='vertical' size={16} style={{ width: '100%' }}><Typography.Title level={4} style={{ margin: 0 }}>小模型分析结果</Typography.Title><Typography.Text type='secondary'>Case: {caseId}</Typography.Text><Card title='结果占位（含 trace/evidence）'><Space size={24}><Statistic title='肺炎风险' value={0.73} precision={2} /><Statistic title='败血风险' value={0.21} precision={2} /></Space><Typography.Paragraph style={{ marginTop: 12, marginBottom: 0 }}>trace_id: trace-demo；evidence_source: lab_panel_v1 + vitals_stream</Typography.Paragraph></Card></Space>;
}
