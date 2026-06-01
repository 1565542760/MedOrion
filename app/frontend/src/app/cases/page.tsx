'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Card, Space, Table, Tag, Typography } from 'antd';
import { listCases } from '@/lib/api';

type CaseRow = {
  case_id: string;
  patient_id?: string;
  disease_task?: string;
  status?: string;
  trace_id?: string;
};

export default function CasesPage() {
  const [rows, setRows] = useState<CaseRow[]>([]);

  useEffect(() => {
    listCases().then((data) => setRows(Array.isArray(data) ? data as CaseRow[] : [])).catch(() => setRows([]));
  }, []);

  return (
    <Space direction='vertical' style={{ width: '100%' }} size={16}>
      <Typography.Title level={4} style={{ margin: 0 }}>患者病例列表</Typography.Title>
      <Card>
        <Table
          rowKey='case_id'
          dataSource={rows}
          pagination={false}
          columns={[
            { title: 'Case ID', dataIndex: 'case_id' },
            { title: 'Patient ID', dataIndex: 'patient_id' },
            { title: 'Task', dataIndex: 'disease_task', render: (v: string) => <Tag>{v}</Tag> },
            { title: 'Status', dataIndex: 'status' },
            { title: 'Trace', dataIndex: 'trace_id' },
            {
              title: '入口',
              render: (_: unknown, row: CaseRow) => <Space>
                <Link href={'/cases/' + row.case_id + '/multimodal'}>多模态</Link>
                <Link href={'/cases/' + row.case_id + '/missing-consultation'}>缺失值</Link>
                <Link href={'/cases/' + row.case_id + '/small-models'}>小模型</Link>
                <Link href={'/cases/' + row.case_id + '/llm-explanation'}>LLM解释</Link>
              </Space>
            }
          ]}
        />
      </Card>
    </Space>
  );
}
