'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Card, Space, Table, Tag, Typography } from 'antd';
import { listCases } from '@/lib/api';

type CaseRow = {
  case_id?: string;
  case_no?: string;
  patient_id?: string;
  disease_task?: string;
  status?: string;
  trace_id?: string;
  key?: string;
};

function makeCaseKey(row: CaseRow) {
  return (
    row.case_id ||
    row.case_no ||
    (row.patient_id && row.trace_id ? row.patient_id + '|' + row.trace_id : '') ||
    [row.patient_id, row.trace_id, row.disease_task, row.status].filter(Boolean).join('|') ||
    JSON.stringify({
      patient_id: row.patient_id || '',
      trace_id: row.trace_id || '',
      disease_task: row.disease_task || '',
      status: row.status || '',
      case_no: row.case_no || '',
    })
  );
}

export default function CasesPage() {
  const [rows, setRows] = useState<CaseRow[]>([]);

  useEffect(() => {
    listCases()
      .then((data) => {
        const normalized = Array.isArray(data)
          ? (data as CaseRow[]).map((row) => ({ ...row, key: makeCaseKey(row) }))
          : [];
        setRows(normalized);
      })
      .catch(() => setRows([]));
  }, []);

  return (
    <Space direction='vertical' style={{ width: '100%' }} size={16}>
      <Typography.Title level={4} style={{ margin: 0 }}>患者病例列表</Typography.Title>
      <Card>
        <Table
          rowKey='key'
          dataSource={rows}
          pagination={false}
          columns={[
            { title: 'Case ID', dataIndex: 'case_id' },
            { title: 'Patient ID', dataIndex: 'patient_id' },
            { title: 'Task', dataIndex: 'disease_task', render: (v: string) => <Tag>{v}</Tag> },
            { title: 'Status', dataIndex: 'status' },
            { title: 'Trace', dataIndex: 'trace_id' },
            {
              title: '操作',
              render: (_: unknown, row: CaseRow) => <Space wrap>
                <Link href={'/cases/' + row.case_id + '/multimodal'}>多模态数据</Link>
                <Link href={'/cases/' + row.case_id + '/missing-consultation'}>缺失值确认</Link>
                <Link href={'/cases/' + row.case_id + '/small-models'}>小模型分析</Link>
                <Link href={'/cases/' + row.case_id + '/llm-explanation'}>大模型解释</Link>
                <Link href={'/cases/' + row.case_id + '/lineage'}>查看溯源</Link>
                <Link href={'/cases/' + row.case_id + '/feedback'}>反馈</Link>
                <Link href={'/cases/' + row.case_id + '/dynamic-monitoring'}>动态监测</Link>
              </Space>
            }
          ]}
        />
      </Card>
    </Space>
  );
}
