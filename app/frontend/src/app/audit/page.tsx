'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Space, Table, Tag, Typography } from 'antd';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
import { listCases, listPatients, listShadowRunsByCase, type CaseItem, type PatientItem, type ShadowInferenceRunItem } from '@/lib/api';

type Row = {
  case_id: string;
  case_no?: string | null;
  patient_name: string;
  patient_identifier: string;
  latest_time: string;
  latest_branch: string;
  latest_status: string;
  run_count: number;
};

function statusTag(value: string) {
  if (value.includes('success')) return <Tag color='green'>已完成</Tag>;
  if (value.includes('failed')) return <Tag color='red'>失败</Tag>;
  if (value.includes('disabled')) return <Tag color='orange'>已跳过</Tag>;
  return <Tag>{value || '无记录'}</Tag>;
}

export default function AuditWorklistPage() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [runs, setRuns] = useState<Record<string, ShadowInferenceRunItem[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [caseItems, patientItems] = await Promise.all([listCases(), listPatients()]);
      setCases(caseItems);
      setPatients(patientItems);
      const pairs = await Promise.all(caseItems.slice(0, 50).map(async (item) => {
        try {
          const response = await listShadowRunsByCase(item.case_id);
          return [item.case_id, response.items || []] as const;
        } catch {
          return [item.case_id, []] as const;
        }
      }));
      setRuns(Object.fromEntries(pairs));
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const patientById = useMemo(() => new Map(patients.map((item) => [item.patient_id, item])), [patients]);
  const rows = useMemo<Row[]>(() => cases.map((item) => {
    const patient = patientById.get(item.patient_id);
    const caseRuns = [...(runs[item.case_id] || [])].sort((a, b) => String(b.started_at || b.created_at || '').localeCompare(String(a.started_at || a.created_at || '')));
    const latest = caseRuns[0];
    return {
      case_id: item.case_id,
      case_no: item.case_no,
      patient_name: patient?.display_name || '未命名患者',
      patient_identifier: patient?.external_patient_id || patient?.patient_id || item.patient_id,
      latest_time: latest?.started_at || latest?.created_at || '-',
      latest_branch: latest?.adapter_code || latest?.model_version_id || '-',
      latest_status: latest?.status || '-',
      run_count: caseRuns.length,
    };
  }), [cases, patientById, runs]);

  const columns = [
    { title: '姓名', dataIndex: 'patient_name', width: 150, fixed: 'left' as const, render: (value: string, row: Row) => <Link href={'/cases/' + row.case_id}>{value}</Link> },
    { title: '患者ID', dataIndex: 'patient_identifier', width: 190, fixed: 'left' as const },
    { title: '住院/门诊号', dataIndex: 'case_no', width: 160, render: (value?: string | null) => value || '-' },
    { title: '最近评估时间', dataIndex: 'latest_time', width: 200 },
    { title: '最近模型分支', dataIndex: 'latest_branch', width: 260 },
    { title: '最近状态', dataIndex: 'latest_status', width: 140, render: statusTag },
    { title: '记录数', dataIndex: 'run_count', width: 100 },
    { title: '操作', width: 150, fixed: 'right' as const, render: (_: unknown, row: Row) => <Link href={'/cases/' + row.case_id + '/shadow-audit'}><Button size='small'>查看审计</Button></Link> },
  ];

  return (
    <main style={{ padding: 24, width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <Space direction='vertical' size={4}>
          <Typography.Title level={3} style={{ margin: 0 }}>审计</Typography.Title>
          <Typography.Text type='secondary'>查看病例模型评估记录，技术细节进入病例审计页右侧详情。</Typography.Text>
        </Space>
        {error ? <Alert type='warning' showIcon message={error} /> : null}
        <WorkspaceTableShell title='审计工作列表' subtitle='全局只展示摘要；每个病例内查看完整评估记录。' actions={<Button onClick={load}>刷新</Button>}>
          <Table rowKey='case_id' loading={loading} columns={columns} dataSource={rows} pagination={false} sticky scroll={{ x: 1320, y: 'calc(100vh - 320px)' }} />
        </WorkspaceTableShell>
      </Space>
    </main>
  );
}
