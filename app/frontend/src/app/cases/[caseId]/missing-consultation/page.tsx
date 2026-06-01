'use client';

import { use, useEffect, useState } from 'react';
import { Card, Space, Table, Tag, Typography } from 'antd';
import { getMissingValues } from '@/lib/api';

type MissingRow = { field: string; reason?: string; suggested_options?: string[] };

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [rows, setRows] = useState<MissingRow[]>([]);

  useEffect(() => {
    getMissingValues(caseId, 'trace-demo').then((data) => setRows(Array.isArray(data) ? data as MissingRow[] : [])).catch(() => setRows([]));
  }, [caseId]);

  return <Space direction='vertical' size={16} style={{ width: '100%' }}><Typography.Title level={4} style={{ margin: 0 }}>缺失值主动咨询</Typography.Title><Typography.Text type='secondary'>Case: {caseId}</Typography.Text><Card><Table rowKey='field' dataSource={rows} pagination={false} columns={[{ title: '字段', dataIndex: 'field' }, { title: '缺失原因', dataIndex: 'reason', render: (v: string) => <Tag color='gold'>{v}</Tag> }, { title: '建议选项', dataIndex: 'suggested_options', render: (v: string[]) => Array.isArray(v) ? v.join(' / ') : '-' }]} /></Card></Space>;
}
