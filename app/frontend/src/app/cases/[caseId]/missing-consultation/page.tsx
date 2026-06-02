'use client';

import { use, useEffect, useState } from 'react';
import { Card, Space, Table, Tag, Typography } from 'antd';
import { getMissingValues } from '@/lib/api';

type MissingRow = {
  field?: string;
  reason?: string;
  suggested_options?: string[];
  route?: string;
  case_id?: string;
  key?: string;
};

function makeMissingKey(row: MissingRow) {
  return (
    row.field ||
    row.route ||
    row.case_id ||
    row.reason ||
    [row.field, row.route, row.case_id, row.reason, ...(row.suggested_options || [])].filter(Boolean).join('|') ||
    JSON.stringify({
      field: row.field || '',
      route: row.route || '',
      case_id: row.case_id || '',
      reason: row.reason || '',
      suggested_options: row.suggested_options || [],
    })
  );
}

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [rows, setRows] = useState<MissingRow[]>([]);

  useEffect(() => {
    getMissingValues(caseId, 'trace-demo')
      .then((data) => {
        const normalized = Array.isArray(data)
          ? data.map((row: MissingRow) => ({ ...row, key: makeMissingKey(row) }))
          : [];
        setRows(normalized);
      })
      .catch(() => setRows([]));
  }, [caseId]);

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>缺失值确认</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}</Typography.Text>
      <Card>
        <Table
          rowKey='key'
          dataSource={rows}
          pagination={false}
          columns={[
            { title: '字段', dataIndex: 'field', render: (v: string) => v || '-' },
            { title: '缺失原因', dataIndex: 'reason', render: (v: string) => <Tag color='gold'>{v || '-'}</Tag> },
            { title: '建议选项', dataIndex: 'suggested_options', render: (v: string[]) => Array.isArray(v) ? v.join(' / ') : '-' },
          ]}
        />
      </Card>
    </Space>
  );
}
