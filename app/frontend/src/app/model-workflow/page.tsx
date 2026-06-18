'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Space, Table, Tag, Typography } from 'antd';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
import { getCapCopShadowWorkflowReadiness, listCases, listPatients, type CaseItem, type CapCopShadowWorkflowReadinessResponse, type PatientItem } from '@/lib/api';

type Row = {
  case_id: string;
  case_no?: string | null;
  patient_name: string;
  patient_identifier: string;
  disease_task?: string | null;
  overall_status: string;
  clinical: string;
  imaging: string;
  multimodal: string;
  next_action: string;
};

function branchStatus(readiness: CapCopShadowWorkflowReadinessResponse | null, key: 'clinical_mlp' | 'imaging_resnet18' | 'multimodal_resnet18') {
  return readiness?.branches?.[key]?.status || 'unknown';
}

function label(value: string) {
  if (value === 'ready' || value === 'ready_all') return <Tag color='green'>可评估</Tag>;
  if (value === 'ready_partial') return <Tag color='blue'>部分可评估</Tag>;
  if (value === 'blocked' || value === 'schema_unverified') return <Tag color='orange'>需补充</Tag>;
  return <Tag>待检查</Tag>;
}

export default function ModelWorkflowWorklistPage() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [readiness, setReadiness] = useState<Record<string, CapCopShadowWorkflowReadinessResponse | null>>({});
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
          return [item.case_id, await getCapCopShadowWorkflowReadiness(item.case_id)] as const;
        } catch {
          return [item.case_id, null] as const;
        }
      }));
      setReadiness(Object.fromEntries(pairs));
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
    const gate = readiness[item.case_id] || null;
    const overall = gate?.overall_status || 'unknown';
    return {
      case_id: item.case_id,
      case_no: item.case_no,
      patient_name: patient?.display_name || '未命名患者',
      patient_identifier: patient?.external_patient_id || patient?.patient_id || item.patient_id,
      disease_task: item.disease_task,
      overall_status: overall,
      clinical: branchStatus(gate, 'clinical_mlp'),
      imaging: branchStatus(gate, 'imaging_resnet18'),
      multimodal: branchStatus(gate, 'multimodal_resnet18'),
      next_action: overall === 'ready_all' || overall === 'ready_partial' ? '进入模型评估' : '补齐输入',
    };
  }), [cases, patientById, readiness]);

  const columns = [
    { title: '姓名', dataIndex: 'patient_name', width: 150, fixed: 'left' as const, render: (value: string, row: Row) => <Link href={'/cases/' + row.case_id}>{value}</Link> },
    { title: '患者ID', dataIndex: 'patient_identifier', width: 190, fixed: 'left' as const },
    { title: '住院/门诊号', dataIndex: 'case_no', width: 160, render: (value?: string | null) => value || '-' },
    { title: '任务', dataIndex: 'disease_task', width: 140, render: (value?: string | null) => value || 'CAP/COP' },
    { title: '整体状态', dataIndex: 'overall_status', width: 150, render: label },
    { title: '临床模型', dataIndex: 'clinical', width: 140, render: label },
    { title: '影像模型', dataIndex: 'imaging', width: 140, render: label },
    { title: '多模态模型', dataIndex: 'multimodal', width: 150, render: label },
    { title: '下一步', dataIndex: 'next_action', width: 160 },
    { title: '操作', width: 170, fixed: 'right' as const, render: (_: unknown, row: Row) => <Link href={'/cases/' + row.case_id + '/model-workflow'}><Button size='small' type='primary'>进入评估</Button></Link> },
  ];

  return (
    <main style={{ padding: 24, width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <Space direction='vertical' size={4}>
          <Typography.Title level={3} style={{ margin: 0 }}>模型评估</Typography.Title>
          <Typography.Text type='secondary'>按患者/病例查看 CAP/COP 三模型评估是否可运行，具体执行在病例内完成。</Typography.Text>
        </Space>
        {error ? <Alert type='warning' showIcon message={error} /> : null}
        <WorkspaceTableShell title='模型评估工作列表' subtitle='一页一个主表格；进入病例后先预览再执行。' actions={<Button onClick={load}>刷新</Button>}>
          <Table rowKey='case_id' loading={loading} columns={columns} dataSource={rows} pagination={false} sticky scroll={{ x: 1500, y: 'calc(100vh - 320px)' }} />
        </WorkspaceTableShell>
      </Space>
    </main>
  );
}
