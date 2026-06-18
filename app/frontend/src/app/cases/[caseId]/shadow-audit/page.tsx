'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { usePathname } from 'next/navigation';
import { useSearchParams } from 'next/navigation';
import { Alert, Button, Descriptions, Drawer, Space, Table, Tag, Typography } from 'antd';
import { CaseSubNav } from '@/components/CaseSubNav';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
import {
  getShadowInferenceRun,
  getShadowRunOutputs,
  listCases,
  listPatients,
  listShadowRunsByCase,
  listShadowRunsByTrace,
  type CaseItem,
  type PatientItem,
  type ShadowInferenceRunItem,
  type ShadowInferenceRunOutputItem,
} from '@/lib/api';

type Row = ShadowInferenceRunItem & { firstOutput?: ShadowInferenceRunOutputItem | null };

function patientName(patient: PatientItem | null) {
  return patient?.display_name || patient?.external_patient_id || '患者';
}

function patientId(patient: PatientItem | null, caseItem: CaseItem | null) {
  return patient?.external_patient_id || caseItem?.patient_id || '-';
}

function branchName(run: ShadowInferenceRunItem) {
  const text = [run.adapter_code, run.model_input_schema_id, run.model_version_id].filter(Boolean).join(' ').toLowerCase();
  if (text.includes('multimodal')) return '多模态模型';
  if (text.includes('imaging')) return '影像模型';
  if (text.includes('clinical')) return '临床模型';
  return run.adapter_code || '模型分支';
}

function statusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'shadow_success': return '已完成';
    case 'shadow_failed': return '失败';
    case 'shadow_disabled': return '已跳过';
    case 'shadow_timeout': return '超时';
    default: return value || '-';
  }
}

function probability(output: ShadowInferenceRunOutputItem | null | undefined, key: string) {
  const value = output?.prediction_probability_json?.[key] ?? output?.prediction_probability_json?.[key.toLowerCase()];
  if (typeof value === 'number') return value.toFixed(3);
  if (typeof value === 'string') return value;
  return '-';
}

function jsonText(value: unknown) {
  if (value === null || value === undefined) return '-';
  return JSON.stringify(value, null, 2);
}

function formatLocalDateTime(value?: string | null) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date).replaceAll('/', '-');
}
export default function ShadowAuditPage() {
  const pathname = usePathname();
  const caseId = useMemo(() => pathname.match(/^\/cases\/([^/]+)/)?.[1] || '', [pathname]);
  const searchParams = useSearchParams();
  const traceId = searchParams.get('trace_id') || '';
  const focusShadowRunId = searchParams.get('shadow_run_id') || '';
  const [caseItem, setCaseItem] = useState<CaseItem | null>(null);
  const [patient, setPatient] = useState<PatientItem | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [selected, setSelected] = useState<Row | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [cases, patients, runList] = await Promise.all([
        listCases(),
        listPatients(),
        traceId ? listShadowRunsByTrace(traceId) : listShadowRunsByCase(caseId),
      ]);
      const foundCase = (cases || []).find((item) => item.case_id === caseId) || null;
      setCaseItem(foundCase);
      setPatient((patients || []).find((item) => item.patient_id === foundCase?.patient_id) || null);
      let nextRuns = runList.items || [];
      if (focusShadowRunId && !nextRuns.some((item) => item.shadow_run_id === focusShadowRunId)) {
        try {
          const run = await getShadowInferenceRun(focusShadowRunId);
          nextRuns = [run, ...nextRuns];
        } catch {}
      }
      const enriched = await Promise.all(nextRuns.map(async (run) => {
        try {
          const outputs = await getShadowRunOutputs(run.shadow_run_id);
          return { ...run, firstOutput: outputs.items?.[0] || null };
        } catch {
          return { ...run, firstOutput: null };
        }
      }));
      const sorted = enriched.sort((a, b) => new Date(b.started_at || b.created_at || 0).getTime() - new Date(a.started_at || a.created_at || 0).getTime());
      setRows(sorted);
      setSelected(sorted.find((item) => item.shadow_run_id === focusShadowRunId) || null);
    } catch {
      setError('审计记录加载失败。');
    } finally {
      setLoading(false);
    }
  }, [caseId, focusShadowRunId, traceId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  const columns = [
    { title: '时间', width: 190, fixed: 'left' as const, render: (_: unknown, row: Row) => formatLocalDateTime(row.started_at || row.created_at) },
    { title: '模型分支', width: 150, render: (_: unknown, row: Row) => branchName(row) },
    { title: '状态', dataIndex: 'status', width: 120, render: (value: string) => <Tag color={value === 'shadow_success' ? 'green' : value === 'shadow_failed' ? 'red' : 'gold'}>{statusLabel(value)}</Tag> },
    { title: '候选标签', width: 120, render: (_: unknown, row: Row) => row.firstOutput?.candidate_label || '-' },
    { title: 'CAP 概率', width: 110, render: (_: unknown, row: Row) => probability(row.firstOutput, 'CAP') },
    { title: 'COP 概率', width: 110, render: (_: unknown, row: Row) => probability(row.firstOutput, 'COP') },
    { title: '输入版本', dataIndex: 'input_snapshot_id', width: 180, render: (value: string | null) => value || '-' },
    { title: '模型版本', dataIndex: 'model_version_id', width: 220 },
    { title: '操作', width: 100, fixed: 'right' as const, render: (_: unknown, row: Row) => <Button size='small' onClick={() => setSelected(row)}>查看</Button> },
  ];

  const previousSameBranch = selected ? rows.find((row) => row.shadow_run_id !== selected.shadow_run_id && branchName(row) === branchName(selected)) : null;

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%' }}>
      <CaseSubNav caseId={caseId} patientName={patientName(patient)} patientId={patientId(patient, caseItem)} caseNo={caseItem?.case_no} />
      {error ? <Alert type='error' showIcon message={error} /> : null}
      <WorkspaceTableShell title='模型审计 / 运行记录' subtitle='这里展示每次模型旁路运行的记录、候选结果和审计详情。' actions={<Space><Button onClick={load}>刷新</Button></Space>}>
        <Table rowKey='shadow_run_id' loading={loading} columns={columns} dataSource={rows} pagination={false} sticky scroll={{ x: 1380, y: 'calc(100vh - 340px)' }} />
      </WorkspaceTableShell>

      <Drawer title='审计详情' width={680} open={!!selected} onClose={() => setSelected(null)}>
        {selected ? (
          <Space direction='vertical' size={16} style={{ width: '100%' }}>
            <Descriptions bordered size='small' column={1}>
              <Descriptions.Item label='模型分支'>{branchName(selected)}</Descriptions.Item>
              <Descriptions.Item label='状态'>{statusLabel(selected.status)}</Descriptions.Item>
              <Descriptions.Item label='审计运行ID'>{selected.shadow_run_id || '-'}</Descriptions.Item>
              <Descriptions.Item label='候选标签'>{selected.firstOutput?.candidate_label || '-'}</Descriptions.Item>
              <Descriptions.Item label='CAP 概率'>{probability(selected.firstOutput, 'CAP')}</Descriptions.Item>
              <Descriptions.Item label='COP 概率'>{probability(selected.firstOutput, 'COP')}</Descriptions.Item>
              <Descriptions.Item label='输入快照'>{selected.input_snapshot_id || '-'}</Descriptions.Item>
              <Descriptions.Item label='模型版本'>{selected.model_version_id || '-'}</Descriptions.Item>
              <Descriptions.Item label='错误码'>{selected.error_code || '-'}</Descriptions.Item>
            </Descriptions>
            <Descriptions bordered size='small' column={1} title='与上一次同模型运行对比'>
              {previousSameBranch ? (
                <>
                  <Descriptions.Item label='上次时间'>{formatLocalDateTime(previousSameBranch.started_at || previousSameBranch.created_at)}</Descriptions.Item>
                  <Descriptions.Item label='上次候选标签'>{previousSameBranch.firstOutput?.candidate_label || '-'}</Descriptions.Item>
                  <Descriptions.Item label='上次概率'>{'CAP ' + probability(previousSameBranch.firstOutput, 'CAP') + ' / COP ' + probability(previousSameBranch.firstOutput, 'COP')}</Descriptions.Item>
                </>
              ) : (
                <Descriptions.Item label='历史运行'>当前病例暂无更早的同模型运行记录</Descriptions.Item>
              )}
            </Descriptions>
            <Typography.Text strong>技术详情</Typography.Text>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#fafafa', border: '1px solid #f0f0f0', padding: 12, borderRadius: 6, maxHeight: 360, overflow: 'auto' }}>
              {jsonText({
                artifact_hash: selected.artifact_hash,
                runtime_env: selected.runtime_env_json,
                preprocessing_summary: selected.firstOutput?.preprocessing_summary,
                raw_output: selected.firstOutput?.prediction_raw_json,
                limitations: selected.firstOutput?.limitations_json,
                error_detail: selected.error_detail_json,
              })}
            </pre>
          </Space>
        ) : null}
      </Drawer>
    </Space>
  );
}
