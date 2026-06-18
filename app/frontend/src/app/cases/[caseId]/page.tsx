'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Alert, Button, Card, Col, Row, Space, Tag, Typography } from 'antd';
import { CaseSubNav } from '@/components/CaseSubNav';
import {
  getCapCopShadowWorkflowReadiness,
  getImagingPreprocessingStatus,
  getModelInputSnapshot,
  getShadowRunOutputs,
  listCaseImagingInputs,
  listCases,
  listModelInputSnapshotsByCase,
  listPatients,
  listShadowRunsByCase,
  type CaseImagingInputItem,
  type CaseItem,
  type CapCopShadowWorkflowBranchReadiness,
  type CapCopShadowWorkflowReadinessResponse,
  type ImagingPreprocessingStatusResponse,
  type ModelInputSnapshotItem,
  type PatientItem,
  type ShadowInferenceRunItem,
  type ShadowInferenceRunOutputItem,
} from '@/lib/api';

type Context = {
  caseItem: CaseItem | null;
  patient: PatientItem | null;
  snapshots: number;
  images: number;
  readiness: CapCopShadowWorkflowReadinessResponse | null;
  latestRun: ShadowInferenceRunItem | null;
  latestOutput: ShadowInferenceRunOutputItem | null;
  latestWorkflowResult: CapCopShadowWorkflowReadinessResponse | null;
  latestSnapshot: ModelInputSnapshotItem | null;
  latestImagingInput: CaseImagingInputItem | null;
  latestImagingStatus: ImagingPreprocessingStatusResponse | null;
};

const branchKeys = ['clinical_mlp', 'imaging_resnet18', 'multimodal_resnet18'] as const;
type BranchKey = (typeof branchKeys)[number];

const branchTitles: Record<BranchKey, string> = {
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

function overallLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'ready_all': return '全部就绪';
    case 'ready_partial': return '部分就绪';
    case 'blocked': return '暂不可运行';
    case 'ready': return '可运行';
    case 'schema_unverified': return '字段契约待复核';
    case 'preprocessing_required': return '需要预处理';
    default: return value || '未知状态';
  }
}

function overallColor(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'ready_all':
    case 'ready': return 'green';
    case 'ready_partial':
    case 'schema_unverified':
    case 'preprocessing_required': return 'gold';
    case 'blocked': return 'red';
    default: return 'blue';
  }
}

function branchStatusLabel(key: BranchKey, value?: string | null, canRun?: boolean) {
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

function branchSummary(branch?: CapCopShadowWorkflowBranchReadiness | null, key?: BranchKey) {
  if (!branch) return '尚无门禁信息';
  if (branch.can_run) {
    if (key === 'clinical_mlp') return '临床单模态允许缺失值，系统会按训练规则处理缺失值。';
    if (key === 'imaging_resnet18') return '影像输入已准备好，下一步可以继续评估。';
    return '临床和影像两侧都已就绪，可以进入多模态评估。';
  }
  const reason = branch.disabled_reasons?.[0] || branch.required_inputs?.[0] || '当前仍有缺口。';
  if (key === 'clinical_mlp') {
    if (reason.includes('schema')) return '字段契约待复核。';
    if (reason.includes('snapshot') || reason.includes('missing')) return '临床输入快照尚未准备好。';
    return '临床输入仍有缺口。';
  }
  if (key === 'imaging_resnet18') {
    if (reason.includes('preprocess')) return '影像尚未完成预处理，需要先完成 DICOM 到 NIfTI 的流程。';
    if (reason.includes('upload')) return '尚未上传 DICOM 文件集合。';
    return '影像输入仍有缺口。';
  }
  return '多模态需要临床和影像同时就绪。';
}

function branchGap(branch?: CapCopShadowWorkflowBranchReadiness | null, key?: BranchKey) {
  if (!branch) return '尚未读取门禁结果';
  if (branch.can_run) {
    if (key === 'clinical_mlp') return '允许缺失值运行';
    if (key === 'imaging_resnet18') return '预处理完成后可运行';
    return '两侧都已就绪';
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
  return '需要临床和影像同时就绪';
}

function probabilityText(output: ShadowInferenceRunOutputItem | null) {
  const map = output?.prediction_probability_json || {};
  const cap = (map as Record<string, unknown>).CAP ?? (map as Record<string, unknown>).cap;
  const cop = (map as Record<string, unknown>).COP ?? (map as Record<string, unknown>).cop;
  const fmt = (value: unknown) => typeof value === 'number' ? value.toFixed(3) : (value ? String(value) : '-');
  return 'CAP ' + fmt(cap) + ' / COP ' + fmt(cop);
}

function snapshotFeature(snapshot: ModelInputSnapshotItem | null, feature: string) {
  const value = snapshot?.mapped_features?.[feature];
  if (value === undefined || value === null || value === '') return '-';
  if (typeof value === 'number') return String(value);
  if (typeof value === 'string') return value;
  return JSON.stringify(value);
}

function imagingStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'completed': return '预处理完成';
    case 'pending': return '待预处理';
    case 'failed': return '预处理失败';
    case 'not_implemented': return '当前为契约占位';
    default: return value || '未知状态';
  }
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

function buildWorkflowResultFromRuns(runs: ShadowInferenceRunItem[], fallback: CapCopShadowWorkflowReadinessResponse | null): CapCopShadowWorkflowReadinessResponse | null {
  if (!runs.length) return fallback;
  const branchMap: Record<BranchKey, CapCopShadowWorkflowBranchReadiness> = {
    clinical_mlp: { status: 'blocked', can_run: false, disabled_reasons: [], required_inputs: [], detected_inputs: [], next_action: '查看临床输入' },
    imaging_resnet18: { status: 'blocked', can_run: false, disabled_reasons: [], required_inputs: [], detected_inputs: [], next_action: '查看影像输入' },
    multimodal_resnet18: { status: 'blocked', can_run: false, disabled_reasons: [], required_inputs: [], detected_inputs: [], next_action: '查看输入准备' },
  };
  let executed = 0;
  for (const run of runs) {
    const key = runBranchKey(run);
    if (!key || branchMap[key].status === 'executed') continue;
    const status = runStatusToBranchStatus(run.status);
    branchMap[key] = {
      status,
      can_run: status === 'executed',
      disabled_reasons: status === 'executed' ? [] : [run.error_code || 'recent_run_unavailable'],
      required_inputs: [],
      detected_inputs: [],
      next_action: status === 'executed' ? '查看审计' : '重新执行',
    };
    if (status === 'executed') executed += 1;
  }
  const overall_status = executed >= 3 ? 'ready_all' : executed > 0 ? 'ready_partial' : 'blocked';
  return {
    status: fallback?.status || overall_status,
    route: fallback?.route || null,
    overall_status,
    branches: branchMap,
  };
}
function nextAction(ctx: Context) {
  const workflowSource = ctx.latestWorkflowResult || ctx.readiness;
  const clinicalReady = !!workflowSource?.branches?.clinical_mlp?.can_run || !!ctx.latestSnapshot;
  const imagingReady = !!workflowSource?.branches?.imaging_resnet18?.can_run || ctx.latestImagingStatus?.preprocessing_status === 'completed' || !!ctx.latestImagingInput;
  const multimodalReady = !!workflowSource?.branches?.multimodal_resnet18?.can_run;
  if (!clinicalReady) return { label: '去补临床输入', href: ctx.caseItem ? '/cases/' + ctx.caseItem.case_id + '/model-input' : null };
  if (!imagingReady) return { label: '上传 DICOM 影像', href: ctx.caseItem ? '/cases/' + ctx.caseItem.case_id + '/imaging-inputs' : null };
  if (multimodalReady && ctx.latestRun) return { label: '查看最新模型评估', href: '/cases/' + ctx.caseItem!.case_id + '/shadow-audit?shadow_run_id=' + ctx.latestRun.shadow_run_id };
  if (multimodalReady) return { label: '查看模型评估', href: ctx.caseItem ? '/cases/' + ctx.caseItem.case_id + '/model-workflow' : null };
  return { label: '预览模型评估流程', href: ctx.caseItem ? '/cases/' + ctx.caseItem.case_id + '/model-workflow' : null };
}
export default function CaseOverviewPage() {
  const pathname = usePathname();
  const caseId = useMemo(() => pathname.match(/^\/cases\/([^/]+)/)?.[1] || '', [pathname]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [ctx, setCtx] = useState<Context>({ caseItem: null, patient: null, snapshots: 0, images: 0, readiness: null, latestRun: null, latestOutput: null, latestWorkflowResult: null, latestSnapshot: null, latestImagingInput: null, latestImagingStatus: null });

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError('');
      try {
        const [cases, patients, snapshots, images, readiness, runs] = await Promise.allSettled([
          listCases(), listPatients(), listModelInputSnapshotsByCase(caseId), listCaseImagingInputs(caseId), getCapCopShadowWorkflowReadiness(caseId), listShadowRunsByCase(caseId),
        ]);
        const caseItem = cases.status === 'fulfilled' ? (cases.value || []).find((item) => item.case_id === caseId) || null : null;
        const patient = patients.status === 'fulfilled' ? (patients.value || []).find((item) => item.patient_id === caseItem?.patient_id) || null : null;
        const runItems = runs.status === 'fulfilled' ? [...(runs.value.items || [])].sort((a, b) => new Date(b.started_at || b.created_at || 0).getTime() - new Date(a.started_at || a.created_at || 0).getTime()) : [];
        const latestRun = runItems[0] || null;
        let latestOutput: ShadowInferenceRunOutputItem | null = null;
        if (latestRun) {
          try {
            const outputs = await getShadowRunOutputs(latestRun.shadow_run_id);
            latestOutput = outputs.items?.[0] || null;
          } catch {
            latestOutput = null;
          }
        }
        const latestSnapshotSummary = snapshots.status === 'fulfilled' ? snapshots.value.items?.[0] || null : null;
        const latestImagingInput = images.status === 'fulfilled' ? images.value.items?.[0] || null : null;
        let latestSnapshot: ModelInputSnapshotItem | null = null;
        let latestImagingStatus: ImagingPreprocessingStatusResponse | null = null;
        if (latestSnapshotSummary) {
          try { latestSnapshot = await getModelInputSnapshot(latestSnapshotSummary.input_snapshot_id); } catch { latestSnapshot = null; }
        }
        if (latestImagingInput) {
          try { latestImagingStatus = await getImagingPreprocessingStatus(latestImagingInput.input_asset_id); } catch { latestImagingStatus = null; }
        }
        const latestWorkflowResult = buildWorkflowResultFromRuns(runItems, readiness.status === 'fulfilled' ? readiness.value : null);
        if (!active) return;
        setCtx({
          caseItem,
          patient,
          snapshots: snapshots.status === 'fulfilled' ? snapshots.value.items.length : 0,
          images: images.status === 'fulfilled' ? images.value.items.length : 0,
          readiness: readiness.status === 'fulfilled' ? readiness.value : null,
          latestRun,
          latestOutput,
          latestWorkflowResult,
          latestSnapshot,
          latestImagingInput,
          latestImagingStatus,
        });
      } catch {
        if (active) setError('病例工作台加载失败，请稍后重试。');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [caseId]);

  const workflowSource = ctx.latestWorkflowResult || ctx.readiness;
  const action = useMemo(() => nextAction(ctx), [ctx]);
  const branches = (workflowSource?.branches || {}) as Record<string, CapCopShadowWorkflowBranchReadiness | null | undefined>;

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <CaseSubNav caseId={caseId} patientName={patientName(ctx.patient)} patientId={patientId(ctx.patient, ctx.caseItem)} caseNo={ctx.caseItem?.case_no} />
      {error ? <Alert type='error' showIcon message={error} /> : null}

      <Card loading={loading} bodyStyle={{ padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <Space direction='vertical' size={6}>
            <Typography.Title level={3} style={{ margin: 0 }}>{patientName(ctx.patient)}</Typography.Title>
            <Space wrap>
              <Tag color='blue'>患者ID：{patientId(ctx.patient, ctx.caseItem)}</Tag>
              <Tag>病例编号：{ctx.caseItem?.case_no || '-'}</Tag>
              <Tag>任务：CAP/COP</Tag>
              <Tag>状态：{ctx.caseItem?.status || '-'}</Tag>
              <Tag color={overallColor(workflowSource?.overall_status)}>总体状态：{overallLabel(workflowSource?.overall_status)}</Tag>
            </Space>
            <Space wrap>
              <Tag color={workflowSource?.branches?.clinical_mlp?.can_run || ctx.latestSnapshot ? 'green' : 'gold'}>临床输入：{ctx.latestSnapshot ? '已有输入快照' : '未见输入快照'}</Tag>
              <Tag color={ctx.latestImagingStatus?.preprocessing_status === 'completed' || ctx.latestImagingInput ? 'green' : 'gold'}>影像输入：{ctx.latestImagingStatus?.preprocessing_status === 'completed' ? '预处理完成' : ctx.latestImagingInput ? '待完成预处理' : '等待影像输入'}</Tag>
              <Tag color={workflowSource?.branches?.multimodal_resnet18?.can_run ? 'green' : 'gold'}>多模态：{workflowSource?.branches?.multimodal_resnet18?.can_run ? '两侧都已就绪' : '仍需临床与影像同时就绪'}</Tag>
            </Space>
          </Space>
          {action.href ? <Button type='primary' href={action.href}>{action.label}</Button> : null}
        </div>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={7}>
          <Card title='下一步任务'>
            <Space direction='vertical' size={8}>
              <Typography.Title level={4} style={{ margin: 0 }}>{action.label}</Typography.Title>
              <Typography.Text type='secondary'>系统会优先提示当前最需要补的输入；临床单模态允许缺失值，影像需要先上传 DICOM 并完成预处理，多模态则要求两侧同时就绪。</Typography.Text>
              {action.href ? <Button type='primary' href={action.href}>前往处理</Button> : null}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={11}>
          <Card title='CAP/COP shadow readiness 工作流'>
            <Space direction='vertical' size={12} style={{ width: '100%' }}>
              {branchKeys.map((key) => {
                const branch = branches[key];
                return (
                  <div key={key} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, borderBottom: '1px solid #f0f0f0', paddingBottom: 10 }}>
                    <Space direction='vertical' size={2} style={{ minWidth: 0 }}>
                      <Typography.Text strong>{branchTitles[key]}</Typography.Text>
                      <Typography.Text type='secondary' style={{ fontSize: 12 }}>{branchSummary(branch, key)}</Typography.Text>
                      <Typography.Text type='secondary' style={{ fontSize: 12 }}>当前缺口：{branchGap(branch, key)}</Typography.Text>
                      <Typography.Text type='secondary' style={{ fontSize: 12 }}>下一步：{branch?.can_run ? '可直接进入评估流程' : key === 'clinical_mlp' ? '去补临床输入' : key === 'imaging_resnet18' ? '去上传 DICOM 影像' : '需要临床和影像同时完成'}</Typography.Text>
                    </Space>
                    <Tag color={branch?.can_run ? 'green' : 'gold'}>{branchStatusLabel(key, branch?.status, branch?.can_run)}</Tag>
                  </div>
                );
              })}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card title='最近模型评估摘要'>
            {ctx.latestRun ? (
              <Space direction='vertical' size={8}>
                <Tag color='blue'>{ctx.latestOutput?.candidate_label ? '候选标签：' + ctx.latestOutput.candidate_label : ctx.latestRun.status}</Tag>
                <Typography.Text>{probabilityText(ctx.latestOutput)}</Typography.Text>
                <Typography.Text type='secondary'>时间：{ctx.latestRun.started_at || ctx.latestRun.created_at || '-'}</Typography.Text>
                <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + ctx.latestRun.shadow_run_id}>查看审计</Link>
              </Space>
            ) : (
              <Typography.Text type='secondary'>暂无最近模型评估，先补输入后再查看评估流程。</Typography.Text>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title='临床输入摘要'>
            <Space direction='vertical' size={8} style={{ width: '100%' }}>
              <Typography.Text>是否已有临床输入快照：{ctx.latestSnapshot ? '是' : '否'}</Typography.Text>
              <Typography.Text>最近更新时间：{ctx.latestSnapshot?.updated_at || ctx.latestSnapshot?.created_at || '-'}</Typography.Text>
              <Typography.Text>当前状态：{ctx.latestSnapshot?.current_assessment_status || ctx.latestSnapshot?.validation_status || '-'}</Typography.Text>
              <Space wrap>
                <Tag>发热：{snapshotFeature(ctx.latestSnapshot, 'Fever')}</Tag>
                <Tag>咳嗽：{snapshotFeature(ctx.latestSnapshot, 'Cough')}</Tag>
                <Tag>咳痰：{snapshotFeature(ctx.latestSnapshot, 'Sputum production (0 none; 1 white; 2 yellow; 3 bloody; 4 not specified; 5 rust-colored; 6 green)')}</Tag>
                <Tag>网格状影：{snapshotFeature(ctx.latestSnapshot, 'Striated_shadow.1')}</Tag>
              </Space>
              <Link href={'/cases/' + caseId + '/model-input'}>进入临床输入继续修改</Link>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title='影像输入摘要'>
            <Space direction='vertical' size={8} style={{ width: '100%' }}>
              <Typography.Text>是否已有影像输入：{ctx.latestImagingInput ? '是' : '否'}</Typography.Text>
              <Typography.Text>预处理状态：{imagingStatusLabel(ctx.latestImagingStatus?.preprocessing_status || null)}</Typography.Text>
              <Typography.Text>最近更新时间：{ctx.latestImagingStatus?.updated_at || ctx.latestImagingInput?.updated_at || ctx.latestImagingInput?.created_at || '-'}</Typography.Text>
              <Typography.Text>是否可进入影像模型评估：{ctx.latestImagingStatus?.preprocessing_status === 'completed' ? '可以' : '需要先完成预处理'}</Typography.Text>
              <Space wrap>
                <Tag>输入方式：{ctx.latestImagingInput?.source_type || ctx.latestImagingStatus?.source_type || '-'}</Tag>
                <Tag>影像输入 ID：{ctx.latestImagingInput?.input_asset_id || ctx.latestImagingStatus?.input_asset_id || '-'}</Tag>
              </Space>
              <Link href={'/cases/' + caseId + '/imaging-inputs'}>进入影像输入继续处理</Link>
            </Space>
          </Card>
        </Col>
      </Row>
      <Card title='当前状态一览' loading={loading}>
        <Space wrap>
          <Tag color={overallColor(workflowSource?.overall_status)}>总体状态：{overallLabel(workflowSource?.overall_status)}</Tag>
          <Tag color={(workflowSource?.branches?.clinical_mlp?.can_run || ctx.latestSnapshot) ? 'green' : 'gold'}>临床输入：{ctx.latestSnapshot ? '已有输入快照' : '未见输入快照'}</Tag>
          <Tag color={(workflowSource?.branches?.imaging_resnet18?.can_run || ctx.latestImagingStatus?.preprocessing_status === 'completed') ? 'green' : 'gold'}>影像输入：{ctx.latestImagingStatus?.preprocessing_status === 'completed' ? '预处理完成' : '待完成预处理'}</Tag>
          <Tag color={workflowSource?.branches?.multimodal_resnet18?.can_run ? 'green' : 'gold'}>多模态：{workflowSource?.branches?.multimodal_resnet18?.can_run ? '两侧都已就绪' : '仍需临床与影像同时就绪'}</Tag>
        </Space>
      </Card>
    </Space>
  );
}
