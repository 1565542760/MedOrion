'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Alert, Button, Card, Modal, Space, Table, Tag, Typography } from 'antd';
import { CaseSubNav } from '@/components/CaseSubNav';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
import {
  executeCapCopShadowWorkflow,
  getCapCopShadowWorkflowReadiness,
  listCases,
  listPatients,
  listShadowRunsByCase,
  getShadowRunOutputs,
  previewCapCopShadowWorkflow,
  type CapCopShadowWorkflowBranchPlan,
  type CapCopShadowWorkflowReadinessResponse,
  type CapCopShadowWorkflowResponse,
  type CaseItem,
  type PatientItem,
  type ShadowInferenceRunItem,
  type ShadowInferenceRunOutputItem,
} from '@/lib/api';

type BranchRow = {
  key: string;
  model: string;
  status: string;
  rawStatus: string;
  canRun: boolean;
  gap: string;
  result: string;
  probability: string;
  shadowRunId?: string | null;
};

const branchKeys = ['clinical_mlp', 'imaging_resnet18', 'multimodal_resnet18'] as const;
type BranchKey = (typeof branchKeys)[number];

const modelLabels: Record<BranchKey, string> = {
  clinical_mlp: 'CAP/COP 临床模型',
  imaging_resnet18: 'CAP/COP 影像模型',
  multimodal_resnet18: 'CAP/COP 多模态模型',
};

function patientName(patient: PatientItem | null) {
  return patient?.display_name || patient?.external_patient_id || '未命名患者';
}

function patientId(patient: PatientItem | null, caseItem: CaseItem | null) {
  return patient?.external_patient_id || caseItem?.patient_id || '-';
}

function statusText(key: BranchKey, value?: string | null, canRun?: boolean) {
  const normalized = (value || '').toLowerCase();
  if (canRun && (!normalized || normalized === 'ready')) {
    return key === 'multimodal_resnet18' ? '可运行（临床 + 影像已就绪）' : key === 'imaging_resnet18' ? '可运行（已完成预处理）' : '可运行（允许缺失值）';
  }
  switch (normalized) {
    case 'ready': return key === 'multimodal_resnet18' ? '可运行（临床 + 影像已就绪）' : key === 'imaging_resnet18' ? '可运行（已完成预处理）' : '可运行（允许缺失值）';
    case 'planned': return '已规划';
    case 'executed': return '已执行';
    case 'skipped': return '已跳过';
    case 'failed': return '执行失败';
    case 'schema_unverified': return '字段契约待复核';
    case 'blocked': return '暂不可运行';
    default: return value || '未知状态';
  }
}

function gapText(key: BranchKey, branch?: CapCopShadowWorkflowBranchPlan | null) {
  if (!branch) return '尚未读取门禁结果';
  if (branch.can_run || branch.status === 'planned' || branch.status === 'executed') {
    return key === 'multimodal_resnet18' ? '临床与影像均已就绪' : key === 'imaging_resnet18' ? '预处理完成后可运行' : '允许缺失值运行';
  }
  const reason = branch.disabled_reasons?.[0] || branch.required_inputs?.[0] || '当前仍有缺口。';
  if (key === 'clinical_mlp') {
    if (reason.includes('schema')) return '字段契约待复核';
    if (reason.includes('snapshot') || reason.includes('missing')) return '临床输入快照未完成';
    return '临床输入缺口';
  }
  if (key === 'imaging_resnet18') {
    if (reason.includes('preprocess')) return '需要先完成 DICOM 预处理';
    if (reason.includes('upload')) return '需要上传 DICOM 文件集合';
    return '影像输入缺口';
  }
  if ((branch?.disabled_reasons || []).some((item) => String(item).includes('missing_snapshot'))) return '多模态暂未执行：输入快照未齐备';
  return '多模态暂未执行：临床与影像结果需先对齐';
}

function probabilityText(value?: Record<string, unknown> | null) {
  if (!value) return '-';
  const cap = value.CAP ?? value.cap;
  const cop = value.COP ?? value.cop;
  const fmt = (item: unknown) => typeof item === 'number' ? item.toFixed(3) : (item ? String(item) : '-');
  return 'CAP ' + fmt(cap) + ' / COP ' + fmt(cop);
}

function runBranchKey(run: ShadowInferenceRunItem): BranchKey | null {
  const text = [run.adapter_code, run.model_input_schema_id, run.model_version_id].filter(Boolean).join(' ').toLowerCase();
  if (text.includes('multimodal')) return 'multimodal_resnet18';
  if (text.includes('imaging')) return 'imaging_resnet18';
  if (text.includes('clinical')) return 'clinical_mlp';
  return null;
}

function runStatusToBranchStatus(status?: string | null) {
  switch ((status || '').toLowerCase()) {
    case 'shadow_success': return 'executed';
    case 'shadow_failed': return 'failed';
    case 'shadow_disabled': return 'skipped';
    default: return 'executed';
  }
}

function buildWorkflowResult(branchMap: Partial<Record<BranchKey, { run: ShadowInferenceRunItem; output: ShadowInferenceRunOutputItem | null }>>): CapCopShadowWorkflowResponse | null {
  const keys = ['clinical_mlp', 'imaging_resnet18', 'multimodal_resnet18'] as const;
  const branches: Record<string, CapCopShadowWorkflowBranchPlan> = {};
  let found = false;
  let executed = 0;
  for (const key of keys) {
    const item = branchMap[key];
    if (!item) {
      branches[key] = { branch: key, status: 'blocked', can_run: false, disabled_reasons: ['no_run_record'], required_inputs: [], detected_inputs: [], next_action: '查看审计' };
      continue;
    }
    found = true;
    const status = runStatusToBranchStatus(item.run.status);
    if (status === 'executed') executed += 1;
    branches[key] = {
      branch: key,
      status,
      can_run: false,
      disabled_reasons: [],
      required_inputs: [],
      detected_inputs: [],
      next_action: '查看审计',
      shadow_run_id: item.run.shadow_run_id,
      output_id: item.output?.output_id || null,
      candidate_label: item.output?.candidate_label || null,
      prediction_probability_json: item.output?.prediction_probability_json || null,
      confidence_json: item.output?.confidence_json ?? null,
      uncertainty_json: item.output?.uncertainty_json ?? null,
      limitations: item.output?.limitations_json || null,
    };
  }
  if (!found) return null;
  const overall_status = executed === keys.length ? 'ready_all' : executed > 0 ? 'ready_partial' : 'blocked';
  return {
    status: overall_status,
    route: null,
    overall_status,
    branches: {
      clinical_mlp: branches.clinical_mlp,
      imaging_resnet18: branches.imaging_resnet18,
      multimodal_resnet18: branches.multimodal_resnet18,
    },
  };
}

function statusTagColor(status: string, canRun?: boolean) {
  const normalized = (status || '').toLowerCase();
  if (normalized === 'executed') return 'green';
  if (normalized === 'skipped') return 'gold';
  if (normalized === 'failed') return 'red';
  if (normalized === 'blocked' || normalized === 'schema_unverified') return 'orange';
  return canRun ? 'green' : 'default';
}

function branchArray(source: CapCopShadowWorkflowReadinessResponse | CapCopShadowWorkflowResponse | null): BranchRow[] {
  const rawBranches = (source as CapCopShadowWorkflowResponse | null)?.branches || (source as CapCopShadowWorkflowResponse | null)?.execution_plan?.branches || (source as CapCopShadowWorkflowResponse | null)?.plan?.branches || (source as CapCopShadowWorkflowReadinessResponse | null)?.branches;
  const branchMap: Partial<Record<BranchKey, CapCopShadowWorkflowBranchPlan>> = {};
  if (Array.isArray(rawBranches)) {
    for (const item of rawBranches) {
      const key = (item.branch || (item as unknown as { key?: string }).key) as BranchKey | undefined;
      if (key) branchMap[key] = item as CapCopShadowWorkflowBranchPlan;
    }
  } else if (rawBranches && typeof rawBranches === 'object') {
    for (const key of branchKeys) {
      branchMap[key] = (rawBranches as Record<string, CapCopShadowWorkflowBranchPlan>)[key] || null;
    }
  }
  return branchKeys.map((key) => {
    let branch: CapCopShadowWorkflowBranchPlan | null = null;
    if (Array.isArray(rawBranches)) {
      branch = (rawBranches.find((item) => item.branch === key || (item as unknown as { key?: string }).key === key) || null) as CapCopShadowWorkflowBranchPlan | null;
    } else if (rawBranches && typeof rawBranches === 'object') {
      branch = (rawBranches as Record<string, CapCopShadowWorkflowBranchPlan>)[key] || null;
    }
    const rawStatus = (branch?.status || branch?.planned_status || '').toLowerCase();
    return {
      key,
      model: modelLabels[key],
      status: statusText(key, rawStatus, branch?.can_run),
      rawStatus,
      canRun: !!branch?.can_run || rawStatus === 'planned' || rawStatus === 'executed',
      gap: gapText(key, branch),
      result: branch?.candidate_label || '-',
      probability: probabilityText(branch?.prediction_probability_json),
      shadowRunId: branch?.shadow_run_id || null,
    };
  });
}
export default function ModelWorkflowPage() {
  const pathname = usePathname();
  const caseId = useMemo(() => pathname.match(/^\/cases\/([^/]+)/)?.[1] || '', [pathname]);
  const [caseItem, setCaseItem] = useState<CaseItem | null>(null);
  const [patient, setPatient] = useState<PatientItem | null>(null);
  const [readiness, setReadiness] = useState<CapCopShadowWorkflowReadinessResponse | null>(null);
  const [preview, setPreview] = useState<CapCopShadowWorkflowResponse | null>(null);
  const [executeResult, setExecuteResult] = useState<CapCopShadowWorkflowResponse | null>(null);
  const [latestWorkflowResult, setLatestWorkflowResult] = useState<CapCopShadowWorkflowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const [casesResult, patientsResult, readyResult, runsResult] = await Promise.allSettled([listCases(), listPatients(), getCapCopShadowWorkflowReadiness(caseId), listShadowRunsByCase(caseId)]);
    const cases = casesResult.status === 'fulfilled' ? casesResult.value : null;
    const patients = patientsResult.status === 'fulfilled' ? patientsResult.value : null;
    const ready = readyResult.status === 'fulfilled' ? readyResult.value : null;
    const foundCase = (cases || []).find((item) => item.case_id === caseId) || null;
    setCaseItem(foundCase);
    setPatient((patients || []).find((item) => item.patient_id === foundCase?.patient_id) || null);
    setReadiness(ready);

    const runItems = runsResult.status === 'fulfilled' ? [...(runsResult.value.items || [])].sort((a, b) => new Date(b.started_at || b.created_at || 0).getTime() - new Date(a.started_at || a.created_at || 0).getTime()) : [];
    const latestByBranch: Partial<Record<BranchKey, { run: ShadowInferenceRunItem; output: ShadowInferenceRunOutputItem | null }>> = {};
    for (const run of runItems) {
      const key = runBranchKey(run);
      if (!key || latestByBranch[key]) continue;
      let output: ShadowInferenceRunOutputItem | null = null;
      try {
        const outputs = await getShadowRunOutputs(run.shadow_run_id);
        output = outputs.items?.[0] || null;
      } catch {
        output = null;
      }
      latestByBranch[key] = { run, output };
    }
    setLatestWorkflowResult(buildWorkflowResult(latestByBranch));
    if (casesResult.status === 'rejected' && patientsResult.status === 'rejected' && readyResult.status === 'rejected' && runsResult.status === 'rejected') {
      setError('模型评估流程加载失败，请稍后重试。');
    }
    setLoading(false);
  }, [caseId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  async function handlePreview() {
    setBusy(true);
    setError('');
    try {
      const data = await previewCapCopShadowWorkflow(caseId, { mode: 'preview' });
      setPreview(data);
      setExecuteResult(null);
    } catch {
      setError('预览失败，请稍后重试。');
    } finally {
      setBusy(false);
    }
  }

  async function handleExecute() {
    Modal.confirm({
      title: '确认执行 CAP/COP 模型评估流程',
      content: '这不是临床诊断，也不是正式推荐。执行后只会写入影子审计，不会写入 trace 或证据链。',
      okText: '确认执行',
      cancelText: '取消',
      onOk: async () => {
        setBusy(true);
        setError('');
        try {
          const data = await executeCapCopShadowWorkflow(caseId, { mode: 'execute' });
          setPreview(null);
          setExecuteResult(data);
          void load();
        } catch {
          setError('执行失败，请稍后重试。');
        } finally {
          setBusy(false);
        }
      },
    });
  }

  const activeSource = executeResult || preview || latestWorkflowResult || readiness;
  const rows = useMemo(() => branchArray(activeSource), [activeSource]);
  const executionSummary = useMemo(() => {
    const summarySource = executeResult || latestWorkflowResult;
    if (!summarySource) return null;
    const branches = branchArray(summarySource);
    const executed = branches.filter((item) => item.rawStatus === 'executed').length;
    const skipped = branches.filter((item) => item.rawStatus === 'skipped').length;
    const failed = branches.filter((item) => item.rawStatus === 'failed').length;
    const allExecuted = executed === branchKeys.length;

    if (failed === branchKeys.length) {
      return {
        color: 'error' as const,
        title: '本次模型评估未完成',
        description: '三个分支都未成功执行，请先检查输入与门禁条件。',
      };
    }

    if (allExecuted) {
      return {
        color: 'success' as const,
        title: '临床、影像与多模态模型均已执行',
        description: '本次执行已经生成三条新的审计记录，可在下方查看。',
      };
    }

    if (executed > 0 && failed > 0) {
      return {
        color: 'warning' as const,
        title: '模型评估部分成功',
        description: '部分分支已成功执行，另有分支执行失败。',
      };
    }
    if (executed > 0 && skipped > 0) {
      return {
        color: 'warning' as const,
        title: '临床与影像模型已执行，多模态因条件不足已跳过',
        description: '这不是整体失败；请在多模态门禁或输入准备完成后再查看。',
      };
    }

    if (executed > 0) {
      return {
        color: 'success' as const,
        title: '模型评估已完成',
        description: '当前结果显示已有分支成功执行。',
      };
    }

    if (skipped > 0) {
      return {
        color: 'warning' as const,
        title: '模型评估存在未执行分支',
        description: '当前结果中有分支尚未执行，但这不代表整次流程失败。',
      };
    }

    return {
      color: 'info' as const,
      title: '模型评估结果已返回',
      description: '可以查看各分支的执行与审计状态。',
    };
  }, [executeResult, latestWorkflowResult]);

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <CaseSubNav caseId={caseId} patientName={patientName(patient)} patientId={patientId(patient, caseItem)} caseNo={caseItem?.case_no} />
      {error ? <Alert type='error' showIcon message={error} /> : null}
      {executionSummary ? <Alert showIcon type={executionSummary.color} message={executionSummary.title} description={executionSummary.description} /> : null}

      <Card loading={loading}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <Space direction='vertical' size={6}>
            <Typography.Title level={4} style={{ margin: 0 }}>CAP/COP 模型评估流程</Typography.Title>
            <Typography.Text type='secondary'>这里展示后端返回的模型评估门禁与执行计划。临床单模态允许缺失值，影像单模态需要先上传 DICOM 并完成预处理，多模态需要两侧同时就绪。</Typography.Text>
            <Space wrap>
              <Tag color='green'>临床单模态：允许缺失值运行</Tag>
              <Tag color='blue'>影像单模态：先上传 DICOM 并预处理</Tag>
              <Tag color='gold'>多模态：临床 + 影像同时就绪</Tag>
            </Space>
          </Space>
          <Space wrap>
            <Button onClick={handlePreview} loading={busy}>预览模型评估流程</Button>
            <Button type='primary' onClick={handleExecute} loading={busy} disabled={!preview}>确认执行</Button>
            <Button href={'/cases/' + caseId + '/shadow-audit'}>查看审计</Button>
          </Space>
        </div>
      </Card>

      <WorkspaceTableShell title='CAP/COP 模型执行计划' subtitle='门禁通过后可以执行，未通过时会展示对应缺口。'>
        <Table
          rowKey='key'
          columns={[
            { title: '模型', dataIndex: 'model', width: 180, fixed: 'left' as const },
            { title: '状态', dataIndex: 'status', width: 180, render: (value: string, row: BranchRow) => <Tag color={statusTagColor(row.rawStatus, row.canRun)}>{value}</Tag> },
            { title: '缺口', dataIndex: 'gap', width: 300 },
            { title: '候选结果', dataIndex: 'result', width: 140 },
            { title: '概率', dataIndex: 'probability', width: 220 },
            { title: '审计', width: 140, render: (_: unknown, row: BranchRow) => row.shadowRunId ? <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + row.shadowRunId}>查看审计</Link> : '-' },
          ]}
          dataSource={rows}
          pagination={false}
          sticky
          scroll={{ x: 1040, y: 'calc(100vh - 380px)' }}
        />
      </WorkspaceTableShell>
    </Space>
  );
}
