'use client';

import Link from 'next/link';
import { use, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Descriptions, Modal, Space, Tabs, Tag, Typography } from 'antd';
import {
  executeCapCopShadowWorkflow,
  getCapCopShadowWorkflowReadiness,
  previewCapCopShadowWorkflow,
  getShadowRunOutputs,
  listCaseImagingInputs,
  listCases,
  listModelInputSnapshotsByCase,
  listPatients,
  listShadowRunsByCase,
  type CaseItem,
  type CapCopShadowWorkflowBranchReadiness,
  type CapCopShadowWorkflowReadinessResponse,
  type CapCopShadowWorkflowResponse,
  type ShadowInferenceRunItem,
  type ShadowInferenceRunOutputItem,
} from '@/lib/api';

type CaseContext = {
  caseItem: CaseItem | null;
  patientDisplayName: string;
  tableSnapshotCount: number;
  imagingInputCount: number;
  latestShadowRun: ShadowInferenceRunItem | null;
  latestShadowOutput: ShadowInferenceRunOutputItem | null;
  latestImagingRun: ShadowInferenceRunItem | null;
  latestImagingOutput: ShadowInferenceRunOutputItem | null;
  loadingError: string;
};

function getCaseStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'open':
      return '进行中';
    case 'closed':
      return '已关闭';
    case 'archived':
      return '已归档';
    case 'draft':
      return '草稿';
    case 'active':
      return '有效';
    default:
      return value || '-';
  }
}

function getDiseaseTaskLabel(value?: string | null) {
  if (!value) return '-';
  if (value === 'cap_cop') return 'CAP/COP';
  if (value === 'UNSPECIFIED') return '未指定';
  return value;
}

function pickPatientDisplayName(patient: { display_name?: string | null; external_patient_id?: string | null } | undefined) {
  return patient?.display_name || patient?.external_patient_id || '-';
}


function getTwinLabel(context: CaseContext) {
  if (context.tableSnapshotCount === 0 && context.imagingInputCount === 0) return '数字孪生待建立';
  if (context.tableSnapshotCount > 0 && context.imagingInputCount === 0) return '表格先行 / 影像待补齐';
  if (context.tableSnapshotCount === 0 && context.imagingInputCount > 0) return '影像已登记 / 表格待补齐';
  if (context.latestShadowRun) return '病例级肺部状态 twin 可查看';
  return '病例级肺部状态 twin 待接入';
}

function isImagingBridgeRun(run: ShadowInferenceRunItem | null) {
  if (!run) return false;
  const haystack = [run.adapter_code, run.model_version_id, run.model_input_schema_id].filter(Boolean).join(' ').toLowerCase();
  return haystack.includes('imaging');
}

function getImagingStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'shadow_disabled':
      return 'Shadow 已禁用';
    case 'shadow_failed':
      return 'Shadow 失败';
    case 'shadow_success':
      return 'Shadow 已完成';
    case 'imaging_runner_not_loaded':
      return '原型未加载';
    case 'prototype_not_executed':
      return '原型未执行';
    case 'real_shadow_executed':
      return '已完成受控 shadow';
    default:
      return value || '-';
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function extractProbabilityMap(value: unknown) {
  return isRecord(value) ? value : {};
}

function getProbability(probabilities: Record<string, unknown>, key: string) {
  const direct = probabilities[key];
  if (direct !== undefined) return direct;
  const upper = probabilities[key.toUpperCase()];
  if (upper !== undefined) return upper;
  const lower = probabilities[key.toLowerCase()];
  if (lower !== undefined) return lower;
  return null;
}

function formatProbability(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    const text = value.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
    return text || '0';
  }
  if (typeof value === 'string' && value.trim()) return value;
  return '-';
}

function getScalarValue(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) return formatProbability(value);
  if (typeof value === 'string' && value.trim()) return value;
  if (isRecord(value) && 'value' in value) return formatProbability(value.value);
  return '-';
}

function renderJsonBlock(value: unknown) {
  return (
    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#fafafa', border: '1px solid #f0f0f0', borderRadius: 6, padding: 12, maxWidth: '100%' }}>
      {typeof value === 'string' ? value : JSON.stringify(value ?? {}, null, 2)}
    </pre>
  );
}

function getImagingCandidateSummary(label?: string | null) {
  if (!label) return '-';
  if (label === 'COP') return 'COP 倾向';
  if (label === 'CAP') return 'CAP 倾向';
  return label;
}

function getWorkflowOverallStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'ready_all':
      return '全部分支可运行';
    case 'ready_partial':
      return '部分分支可运行';
    case 'blocked':
      return '当前不可运行';
    default:
      return value || 'readiness 暂不可用';
  }
}

function getWorkflowBranchStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'ready':
      return '可运行';
    case 'blocked':
      return '不可运行';
    case 'disabled':
      return '已禁用';
    case 'schema_unverified':
      return 'schema 未验证';
    case 'need_preprocessing':
      return '需要预处理';
    case 'prototype_only':
      return '仅原型';
    default:
      return value || '不可运行';
  }
}

function resolveWorkflowNextAction(caseId: string, nextAction?: string | null) {
  const raw = (nextAction || '').trim();
  const lower = raw.toLowerCase();
  if (!raw) {
    return { label: '继续补齐输入', href: null as string | null, hint: '后端未提供下一步' };
  }
  if (lower.includes('/model-input')) {
    return { label: '进入临床输入', href: '/cases/' + caseId + '/model-input', hint: raw };
  }
  if (lower.includes('/imaging-inputs')) {
    return { label: '进入影像输入', href: '/cases/' + caseId + '/imaging-inputs', hint: raw };
  }
  if (lower.includes('/multimodal')) {
    return { label: '进入多模态页面', href: '/cases/' + caseId + '/multimodal', hint: raw };
  }
  if (lower.includes('preprocess')) {
    return { label: '进入影像输入', href: '/cases/' + caseId + '/imaging-inputs', hint: raw };
  }
  return { label: raw, href: null as string | null, hint: raw };
}

function getWorkflowGapLabel(key: string, disabledReasons: string[], requiredInputs: string[]) {
  const reason = disabledReasons[0] || requiredInputs[0] || '';
  const lower = reason.toLowerCase();
  if (key === 'clinical_mlp') {
    if (lower.includes('schema_unverified')) return '临床输入契约待复核';
    if (lower.includes('snapshot')) return '临床 36 特征快照待补齐';
    return '临床输入待补齐';
  }
  if (key === 'imaging_resnet18') {
    if (lower.includes('preprocess')) return '影像预处理待完成';
    if (lower.includes('nifti') || lower.includes('image.nii.gz')) return '需要 image.nii.gz';
    return '影像输入待补齐';
  }
  if (key === 'multimodal_resnet18') {
    if (lower.includes('schema_unverified')) return '临床输入契约待复核';
    if (lower.includes('image.nii.gz')) return '临床 + 影像都要先准备好';
    return '多模态输入待补齐';
  }
  return '当前门禁暂不满足';
}

function stringifyWorkflowList(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.map((item) => String(item));
  if (typeof value === 'string') return value.trim() ? [value] : [];
  if (typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, item]) => {
      if (item === null || item === undefined || item === false) return [];
      if (item === true) return [key];
      if (Array.isArray(item)) return item.map((entry) => key + ': ' + String(entry));
      if (typeof item === 'object') return [key + ': ' + JSON.stringify(item)];
      return [key + ': ' + String(item)];
    });
  }
  return [String(value)];
}

function getWorkflowPlanStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'ready':
    case 'planned':
      return '计划执行';
    case 'executed':
      return '已执行';
    case 'skipped':
      return '已跳过';
    case 'failed':
      return '执行失败';
    case 'ready_all':
      return '全部分支可运行';
    case 'ready_partial':
      return '部分分支可运行';
    case 'blocked':
      return '当前不可运行';
    case 'disabled':
      return '已禁用';
    case 'schema_unverified':
      return 'schema 未验证';
    case 'need_preprocessing':
      return '需要预处理';
    case 'prototype_only':
      return '仅原型';
    default:
      return value || '不可运行';
  }
}

function getWorkflowPlanStatusColor(value?: string | null, canRun?: boolean) {
  switch ((value || '').toLowerCase()) {
    case 'executed':
    case 'ready':
    case 'planned':
    case 'ready_all':
      return 'green';
    case 'ready_partial':
      return 'blue';
    case 'skipped':
      return 'gold';
    case 'failed':
      return 'red';
    default:
      return canRun ? 'green' : 'default';
  }
}

function getWorkflowProbabilitySummary(probabilityJson: unknown) {
  if (!isRecord(probabilityJson)) return '-';
  const cap = getProbability(probabilityJson, 'CAP');
  const cop = getProbability(probabilityJson, 'COP');
  if (cap !== null || cop !== null) {
    return 'CAP=' + formatProbability(cap) + ' / COP=' + formatProbability(cop);
  }
  return JSON.stringify(probabilityJson);
}

function getWorkflowConfidenceSummary(confidenceJson: unknown) {
  return getScalarValue(confidenceJson);
}

function getWorkflowBranchEntry(source: CapCopShadowWorkflowResponse | CapCopShadowWorkflowReadinessResponse | null | undefined, key: string) {
  const workflowSource = source as Record<string, unknown> & {
    execution_plan?: { branches?: unknown };
    plan?: { branches?: unknown };
    branches?: unknown;
    result?: { branches?: unknown };
  };
  const possible = [workflowSource?.execution_plan?.branches, workflowSource?.plan?.branches, workflowSource?.branches, workflowSource?.result?.branches];
  for (const item of possible) {
    if (!item) continue;
    if (Array.isArray(item)) {
      const found = item.find((branch) => String((branch as Record<string, unknown>).branch || (branch as Record<string, unknown>).key || '') === key);
      if (found) return found as Record<string, unknown>;
    } else if (typeof item === 'object') {
      const branch = (item as Record<string, unknown>)[key];
      if (branch) return branch as Record<string, unknown>;
    }
  }
  return null;
}

function buildWorkflowBranchView(caseId: string, key: string, title: string, source: CapCopShadowWorkflowResponse | CapCopShadowWorkflowReadinessResponse | null | undefined, fallbackRequirement: string, fallbackNextHint: string) {
  const branch = getWorkflowBranchEntry(source, key) || {};
  const canRun = Boolean(branch.can_run);
  const status = String(branch.status || (canRun ? 'planned' : 'skipped'));
  const disabledReasons = stringifyWorkflowList(branch.disabled_reasons);
  const requiredInputs = stringifyWorkflowList(branch.required_inputs);
  const detectedInputs = stringifyWorkflowList(branch.detected_inputs);
  const nextAction = resolveWorkflowNextAction(caseId, typeof branch.next_action === 'string' ? branch.next_action : null);
  const limitations = stringifyWorkflowList(branch.limitations || disabledReasons);
  const gapLabel = getWorkflowGapLabel(key, disabledReasons, requiredInputs);
  return {
    key,
    title,
    status,
    statusColor: getWorkflowPlanStatusColor(status, canRun),
    canRun,
    disabledReasons,
    gapLabel,
    requiredInputs: requiredInputs.length ? requiredInputs : [fallbackRequirement],
    detectedInputs,
    nextActionLabel: nextAction.label,
    nextActionHref: nextAction.href,
    nextActionHint: nextAction.hint || fallbackNextHint,
    limitations,
    shadowRunId: typeof branch.shadow_run_id === 'string' ? branch.shadow_run_id : null,
    outputId: typeof branch.output_id === 'string' ? branch.output_id : null,
    candidateLabel: typeof branch.candidate_label === 'string' ? branch.candidate_label : null,
    probabilitySummary: getWorkflowProbabilitySummary(branch.prediction_probability_json),
    confidenceSummary: getWorkflowConfidenceSummary(branch.confidence_json),
    uncertaintySummary: getWorkflowConfidenceSummary(branch.uncertainty_json),
    note: typeof branch.note === 'string' ? branch.note : (typeof branch.skipped_reason === 'string' ? branch.skipped_reason : ''),
  };
}

function normalizeWorkflowBranches(caseId: string, source: CapCopShadowWorkflowResponse | CapCopShadowWorkflowReadinessResponse | null | undefined) {
  return [
    buildWorkflowBranchView(caseId, 'clinical_mlp', 'clinical MLP', source, '需要 36-feature artifact-order snapshot', '进入临床输入 / 输入快照'),
    buildWorkflowBranchView(caseId, 'imaging_resnet18', 'imaging ResNet18', source, '需要预处理后的 image.nii.gz', '进入影像输入 / 预处理契约'),
    buildWorkflowBranchView(caseId, 'multimodal_resnet18', 'multimodal ResNet18', source, '需要 clinical snapshot + image.nii.gz', '补齐临床 + 影像后再进入多模态'),
  ];
}

export default function CaseWorkbenchPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [context, setContext] = useState<CaseContext>({
    caseItem: null,
    patientDisplayName: '-',
    tableSnapshotCount: 0,
    imagingInputCount: 0,
    latestShadowRun: null,
    latestShadowOutput: null,
    latestImagingRun: null,
    latestImagingOutput: null,
    loadingError: '',
  });
  const [loading, setLoading] = useState(true);
  const [workflowReadiness, setWorkflowReadiness] = useState<CapCopShadowWorkflowReadinessResponse | null>(null);
  const [workflowReadinessError, setWorkflowReadinessError] = useState('');
  const [workflowPreview, setWorkflowPreview] = useState<CapCopShadowWorkflowResponse | null>(null);
  const [workflowPreviewLoading, setWorkflowPreviewLoading] = useState(false);
  const [workflowPreviewError, setWorkflowPreviewError] = useState('');
  const [workflowExecuteResult, setWorkflowExecuteResult] = useState<CapCopShadowWorkflowResponse | null>(null);
  const [workflowExecuteLoading, setWorkflowExecuteLoading] = useState(false);
  const [workflowExecuteError, setWorkflowExecuteError] = useState('');

  const latestShadowRunId = context.latestShadowRun?.shadow_run_id || '';
  const latestShadowCandidate = context.latestShadowOutput?.candidate_label || '';
  const innerBlockStyle = { border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff', minWidth: 0 };
  const loadingBanner = loading ? (
    <Alert type='info' showIcon message='病例工作台加载中' description='正在汇总表格输入、影像输入和 Shadow 状态。' />
  ) : null;

  useEffect(() => {
    let active = true;
    void (async () => {
      await Promise.resolve();
      if (!active) return;
      setLoading(true);
      setWorkflowReadiness(null);
      setWorkflowReadinessError('');
      setWorkflowPreview(null);
      setWorkflowPreviewError('');
      setWorkflowExecuteResult(null);
      setWorkflowExecuteLoading(false);
      setWorkflowExecuteError('');
      try {
        const [casesResult, patientsResult, snapshotResult, imagingResult, shadowResult, workflowResult] = await Promise.allSettled([
          listCases(),
          listPatients(),
          listModelInputSnapshotsByCase(caseId),
          listCaseImagingInputs(caseId),
          listShadowRunsByCase(caseId),
          getCapCopShadowWorkflowReadiness(caseId),
        ]);

        if (!active) return;

        const caseItem = casesResult.status === 'fulfilled'
          ? (casesResult.value || []).find((item) => item.case_id === caseId) || null
          : null;
        const patientMap = patientsResult.status === 'fulfilled'
          ? new Map(patientsResult.value.map((item) => [item.patient_id, pickPatientDisplayName(item)]))
          : new Map<string, string>();
        const snapshots = snapshotResult.status === 'fulfilled' ? snapshotResult.value.items || [] : [];
        const imagingInputs = imagingResult.status === 'fulfilled' ? imagingResult.value.items || [] : [];
        const shadowRuns = shadowResult.status === 'fulfilled' ? shadowResult.value.items || [] : [];
        const latestShadowRun = [...shadowRuns].sort(
          (a, b) => new Date(b.started_at || b.created_at || 0).getTime() - new Date(a.started_at || a.created_at || 0).getTime(),
        )[0] || null;
        const latestShadowOutput = latestShadowRun
          ? (await getShadowRunOutputs(latestShadowRun.shadow_run_id).catch(() => ({ items: [] as ShadowInferenceRunOutputItem[], total: 0 }))).items?.[0] || null
          : null;
        const latestImagingRun = [...shadowRuns]
          .filter(isImagingBridgeRun)
          .sort((a, b) => new Date(b.started_at || b.created_at || 0).getTime() - new Date(a.started_at || a.created_at || 0).getTime())[0] || null;
        const latestImagingOutput = latestImagingRun
          ? (await getShadowRunOutputs(latestImagingRun.shadow_run_id).catch(() => ({ items: [] as ShadowInferenceRunOutputItem[], total: 0 }))).items?.[0] || null
          : null;

        setContext({
          caseItem,
          patientDisplayName: caseItem ? (patientMap.get(caseItem.patient_id) || '-') : '-',
          tableSnapshotCount: snapshots.length,
          imagingInputCount: imagingInputs.length,
          latestShadowRun,
          latestShadowOutput,
          latestImagingRun,
          latestImagingOutput,
          loadingError: '',
        });
        if (workflowResult.status === 'fulfilled') {
          setWorkflowReadiness(workflowResult.value);
          setWorkflowReadinessError('');
        } else {
          setWorkflowReadiness(null);
          setWorkflowReadinessError('readiness 暂不可用，后端 gate 读取失败。');
        }
      } catch {
        if (!active) return;
        setContext((current) => ({ ...current, loadingError: '病例工作台加载失败，请确认后端服务和登录状态。' }));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [caseId]);

  const headerSummary = useMemo(() => [
    { label: '患者姓名 / 显示名', value: context.patientDisplayName || '-' },
    { label: '病例编号', value: context.caseItem?.case_no || '-' },
    { label: '病种任务', value: getDiseaseTaskLabel(context.caseItem?.disease_task) },
    { label: '当前病例状态', value: getCaseStatusLabel(context.caseItem?.status) },
  ], [context.caseItem, context.patientDisplayName]);

  const overviewCards = [
    {
      title: '表格输入状态',
      badge: context.tableSnapshotCount > 0 ? '已登记' : '待补齐',
      description: context.tableSnapshotCount > 0 ? '已有表格输入快照，可继续做模型预览和 shadow 审计。' : '请先进入“输入数据”补齐表格特征与输入快照。',
    },
    {
      title: '影像输入状态',
      badge: context.imagingInputCount > 0 ? '已登记' : '待登记',
      description: context.imagingInputCount > 0 ? '已有影像 metadata / reference 登记。' : '请先进入“输入数据”登记影像输入 / 引用。',
    },
    {
      title: 'clinical MLP shadow 状态',
      badge: context.latestShadowRun ? '旁路已完成' : 'schema_unverified / 待接入',
      description: context.latestShadowRun
        ? ('结果只用于 shadow 审计和医生复核，不能当作诊断或正式推荐。' + (latestShadowCandidate ? ' 当前候选标签：' + latestShadowCandidate + '。' : ''))
        : '当前仍是 tabular baseline，schema_unverified 风险仍需保留。',
    },
    {
      title: 'imaging ResNet18 shadow 状态',
      badge: context.latestImagingRun
        ? (context.latestImagingRun.status === 'shadow_success' && context.latestImagingOutput
          ? '已完成受控 shadow'
          : getImagingStatusLabel(context.latestImagingRun.status))
        : '原型候选 / 未执行',
      description: context.latestImagingRun
        ? (context.latestImagingRun.status === 'shadow_success' && context.latestImagingOutput
          ? '已接通原型 runner，当前有受控 real-shadow 结果，但仍然是 synthetic-only / coursework_mvp / not_for_diagnosis。'
          : '当前只保留原型与桥接位置，不把它包装成真实结果。')
        : '当前只有 artifact preflight 和 runner prototype candidate，前端不把它包装成真实结果。',
    },
    {
      title: 'multimodal ResNet18 shadow 状态',
      badge: '待接入',
      description: '多模态融合入口先保留位置，不在本阶段触发任何运行。',
    },
    {
      title: '数字孪生状态',
      badge: getTwinLabel(context),
      description: '病例级 lung-state twin 只用于课程演示与审计展示，不是诊断图。',
    },
  ];




  const workflowGateData = useMemo(() => {
    const buildFallbackBranch = (title: string, requirement: string, nextHref: string, nextHint: string) => ({
      title,
      info: {
        state: '不可运行',
        stateColor: 'default',
        requirement,
        gap: workflowReadinessError || 'readiness 暂不可用，后端 gate 读取失败。',
        nextLabel: nextHint,
        nextHref,
        note: '当前仅保留门禁骨架，不自算 readiness。',
      },
      nextHint,
      canRun: false,
      disabledReasons: [workflowReadinessError || 'readiness 暂不可用，后端 gate 读取失败。'],
      requiredInputs: [requirement],
      detectedInputs: [],
    });

    if (!workflowReadiness) {
      return {
        workflowAnyReady: false,
        workflowFullyReady: false,
        workflowGateLabel: 'readiness 暂不可用',
        workflowGateMessage: workflowReadinessError || '后端 gate 暂不可用，当前只保留只读门禁骨架。',
        workflowGateBlockers: [workflowReadinessError || 'readiness 暂不可用，后端 gate 读取失败。'],
        workflowBranches: [
          buildFallbackBranch('clinical MLP', '需要 36-feature artifact-order snapshot', '/cases/' + caseId + '/model-input', '进入临床输入 / 输入快照'),
          buildFallbackBranch('imaging ResNet18', '需要预处理后的 image.nii.gz', '/cases/' + caseId + '/imaging-inputs', '进入影像输入 / 预处理契约'),
          buildFallbackBranch('multimodal ResNet18', '需要 clinical snapshot + image.nii.gz', '/cases/' + caseId + '/model-input', '补齐临床 + 影像后再进入多模态'),
        ],
      };
    }

    const buildBranch = (
      title: string,
      branch: CapCopShadowWorkflowBranchReadiness | null | undefined,
      nextHint: string,
      fallbackRequirement: string,
    ) => {
      const next = resolveWorkflowNextAction(caseId, branch?.next_action);
      const disabledReasons = branch?.disabled_reasons || [];
      const requiredInputs = branch?.required_inputs || [];
      const detectedInputs = branch?.detected_inputs || [];
      const canRun = !!branch?.can_run;
      return {
        key: title,
        title,
        info: {
          state: getWorkflowBranchStatusLabel(branch?.status || (canRun ? 'ready' : 'blocked')),
          stateColor: canRun ? 'green' : 'default',
          requirement: requiredInputs.length ? requiredInputs.join(' / ') : fallbackRequirement,
          gap: disabledReasons.length ? disabledReasons.join('\uFF1B') : (detectedInputs.length ? detectedInputs.join('\uFF1B') : '\u540e\u7aef\u672a\u8fd4\u56de detected_inputs'),
          nextLabel: next.label,
          nextHref: next.href || (nextHint.startsWith('/') ? nextHint : ''),
          note: next.hint,
        },
        nextHint,
        canRun,
        disabledReasons,
        requiredInputs,
        detectedInputs,
      };
    };

    const workflowBranches = [
      buildBranch('clinical MLP', workflowReadiness.branches.clinical_mlp, '进入临床输入 / 输入快照', '需要 36-feature artifact-order snapshot'),
      buildBranch('imaging ResNet18', workflowReadiness.branches.imaging_resnet18, '进入影像输入 / 预处理契约', '需要预处理后的 image.nii.gz'),
      buildBranch('multimodal ResNet18', workflowReadiness.branches.multimodal_resnet18, '补齐临床 + 影像后再进入多模态', '需要 clinical snapshot + image.nii.gz'),
    ];
    const workflowAnyReady = workflowBranches.some((item) => item.canRun);
    const workflowFullyReady = workflowBranches.every((item) => item.canRun);
    const workflowGateLabel = getWorkflowOverallStatusLabel(workflowReadiness.overall_status);
    const workflowGateMessage = workflowReadiness.route ? `后端 gate 已返回：${workflowReadiness.route}` : '后端 gate 已返回。';
    const workflowGateBlockers = workflowBranches.flatMap((item) => item.disabledReasons.length > 0 ? item.disabledReasons : []).filter(Boolean);
    return {
      workflowAnyReady,
      workflowFullyReady,
      workflowGateLabel,
      workflowGateMessage,
      workflowGateBlockers,
      workflowBranches,
    };
  }, [caseId, workflowReadiness, workflowReadinessError]);

  const {
    workflowAnyReady,
    workflowFullyReady,
    workflowGateLabel,
    workflowGateMessage,
    workflowGateBlockers,
    workflowBranches,
  } = workflowGateData;

  const workflowPreviewBranches = useMemo(() => (workflowPreview ? normalizeWorkflowBranches(caseId, workflowPreview) : []) as ReturnType<typeof normalizeWorkflowBranches>, [caseId, workflowPreview]);
  const workflowActionCanExecute = Boolean(workflowPreview && workflowPreviewBranches.some((branch) => branch.canRun));

  const handleWorkflowPreview = async () => {
    setWorkflowPreviewLoading(true);
    setWorkflowPreviewError('');
    setWorkflowExecuteResult(null);
    setWorkflowExecuteError('');
    try {
      const result = await previewCapCopShadowWorkflow(caseId);
      setWorkflowPreview(result);
    } catch {
      setWorkflowPreview(null);
      setWorkflowPreviewError('后端暂时无法返回 workflow 预览，请稍后再试。');
    } finally {
      setWorkflowPreviewLoading(false);
    }
  };

  const handleWorkflowExecute = () => {
    Modal.confirm({
      title: '确认执行 CAP/COP shadow workflow',
      centered: true,
      width: 640,
      okText: '确认执行',
      cancelText: '取消',
      content: (
        <Space direction='vertical' size={8} style={{ width: '100%' }}>
          <Typography.Text>这一步不会生成诊断结论，也不是正式推荐。</Typography.Text>
          <Typography.Text>只会写 shadow audit，不写 trace / evidence。</Typography.Text>
          <Typography.Text>概率未校准，请先确认 preview 结果。</Typography.Text>
        </Space>
      ),
      onOk: async () => {
        setWorkflowExecuteLoading(true);
        setWorkflowExecuteError('');
        try {
          const result = await executeCapCopShadowWorkflow(caseId, { mode: 'execute' });
          setWorkflowExecuteResult(result);
        } catch {
          setWorkflowExecuteResult(null);
          setWorkflowExecuteError('后端暂时无法执行 workflow，请稍后再试。');
          throw new Error('workflow execute failed');
        } finally {
          setWorkflowExecuteLoading(false);
        }
      },
    });
  };



  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      {loadingBanner}
      <Card size='small' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Space wrap size={8}>
            <Typography.Title level={5} style={{ margin: 0 }}>病例摘要与门禁</Typography.Title>
            <Tag color={workflowFullyReady ? 'green' : workflowAnyReady ? 'blue' : 'red'}>{workflowGateLabel}</Tag>
            <Tag color='gold'>Shadow only</Tag>
            <Tag color='gold'>非诊断</Tag>
            <Tag color='gold'>非正式推荐</Tag>
          </Space>
          <Descriptions bordered size='small' column={2}>
            {headerSummary.map((item) => (
              <Descriptions.Item label={item.label} key={item.label}>{item.value}</Descriptions.Item>
            ))}
          </Descriptions>
          <Alert
            type='info'
            showIcon
            message='仅用于科研与辅助评估，不作为临床诊断依据'
            description={context.caseItem?.chief_complaint ? `主诉：${context.caseItem.chief_complaint}` : '病例工作台把患者摘要、输入状态、模型可运行性和下一步入口收拢在一屏。'}
          />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, width: '100%' }}>
            {workflowBranches.map((item) => (
              <div key={item.title} style={innerBlockStyle}>
                <Space direction='vertical' size={6} style={{ width: '100%' }}>
                  <Space wrap size={6}>
                    <Typography.Text strong>{item.title}</Typography.Text>
                    <Tag color={item.canRun ? 'green' : 'default'}>{item.canRun ? '可运行' : '不可运行'}</Tag>
                    <Tag color={item.canRun ? 'green' : 'gold'}>{item.info.state}</Tag>
                  </Space>
                  <Typography.Text type='secondary'>输入要求：{item.info.requirement}</Typography.Text>
                  <Typography.Text>缺什么：{item.disabledReasons.join('；') || item.info.note || '无'}</Typography.Text>
                  <Typography.Text type='secondary'>下一步：{item.nextHint}</Typography.Text>
                  {item.info.nextHref ? <Link href={item.info.nextHref}>{item.info.nextLabel}</Link> : <Typography.Text type='secondary'>{item.info.nextLabel}</Typography.Text>}
                </Space>
              </div>
            ))}
          </div>
          <Alert
            type={workflowAnyReady ? 'info' : 'warning'}
            showIcon
            message={workflowFullyReady ? '门禁已满足，可先预览再确认执行。' : workflowAnyReady ? '部分分支可运行，请先预览再确认执行。' : '当前还不能执行模型评估。'}
            description={workflowGateMessage}
          />
          {workflowGateBlockers.length > 0 ? (
            <Alert
              type='warning'
              showIcon
              message='为什么现在不能运行'
              description={(
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {workflowGateBlockers.map((reason) => <li key={reason}>{reason}</li>)}
                </ul>
              )}
            />
          ) : null}
          <Space wrap size={8}>
            <Button type='primary' loading={workflowPreviewLoading} onClick={handleWorkflowPreview}>预览模型评估流程</Button>
            <Button disabled={!workflowPreview || !workflowActionCanExecute} loading={workflowExecuteLoading} onClick={handleWorkflowExecute}>确认执行模型评估流程</Button>
          </Space>
          <Typography.Text type='secondary'>执行按钮会在预览后解锁；执行仅写审计记录，不作为正式结果。</Typography.Text>
          {workflowPreviewError ? <Alert type='error' showIcon message={workflowPreviewError} /> : null}
          {workflowExecuteError ? <Alert type='error' showIcon message={workflowExecuteError} /> : null}
          {workflowPreview ? (
            <Alert
              type='success'
              showIcon
              message={'预览结果：' + getWorkflowPlanStatusLabel(workflowPreview.overall_status || workflowPreview.status || null)}
              description='预览只生成执行计划，不会改变审计记录。'
            />
          ) : null}
          {workflowExecuteResult ? (
            <Alert
              type='success'
              showIcon
              message={'执行结果：' + getWorkflowPlanStatusLabel(workflowExecuteResult.overall_status || workflowExecuteResult.status || null)}
              description='执行结果仍然只写审计记录。'
            />
          ) : null}
        </Space>
      </Card>



      <Tabs
        destroyInactiveTabPane={false}
        items={[
          {
            key: 'overview',
            label: '总览',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='info'
                  showIcon
                  message='一屏只看摘要'
                  description='更细的表格、输入映射、审计与技术字段都留在对应页面。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, width: '100%' }}>
                  {overviewCards.map((item) => (
                    <div key={item.title} style={innerBlockStyle}>
                      <Space direction='vertical' size={4}>
                        <Typography.Text type='secondary'>{item.title}</Typography.Text>
                        <Tag color='blue'>{item.badge}</Tag>
                        <Typography.Text>{item.description}</Typography.Text>
                      </Space>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={innerBlockStyle}>
                    <Space direction='vertical' size={6} style={{ width: '100%' }}>
                      <Typography.Text type='secondary'>最近的临床模型概要</Typography.Text>
                      {context.latestShadowRun ? (
                        <>
                          <Tag color='green'>{getImagingStatusLabel(context.latestShadowRun.status)}</Tag>
                          <Typography.Text>候选标签：{context.latestShadowOutput?.candidate_label || '暂无'}</Typography.Text>
                          <Typography.Text>概率：{context.latestShadowOutput ? getWorkflowProbabilitySummary(context.latestShadowOutput.prediction_probability_json) : '暂无'}</Typography.Text>
                          <Typography.Text type='secondary'>时间：{context.latestShadowRun.started_at || context.latestShadowRun.created_at || '-'}</Typography.Text>
                          <Link href={latestShadowRunId ? '/cases/' + caseId + '/shadow-audit?shadow_run_id=' + latestShadowRunId : '/cases/' + caseId + '/shadow-audit'}>查看审计</Link>
                        </>
                      ) : (
                        <Typography.Text type='secondary'>暂无记录，请先补齐输入。</Typography.Text>
                      )}
                    </Space>
                  </div>
                  <div style={innerBlockStyle}>
                    <Space direction='vertical' size={6} style={{ width: '100%' }}>
                      <Typography.Text type='secondary'>最近的影像模型概要</Typography.Text>
                      {context.latestImagingRun ? (
                        <>
                          <Tag color={context.latestImagingRun.status === 'shadow_success' && context.latestImagingOutput ? 'green' : 'gold'}>{getImagingStatusLabel(context.latestImagingRun.status)}</Tag>
                          <Typography.Text>候选标签：{context.latestImagingOutput ? getImagingCandidateSummary(context.latestImagingOutput.candidate_label) : '暂无'}</Typography.Text>
                          <Typography.Text>概率：{context.latestImagingOutput ? getWorkflowProbabilitySummary(context.latestImagingOutput.prediction_probability_json) : '暂无'}</Typography.Text>
                          <Typography.Text type='secondary'>时间：{context.latestImagingRun.started_at || context.latestImagingRun.created_at || '-'}</Typography.Text>
                          <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + context.latestImagingRun.shadow_run_id}>查看审计</Link>
                        </>
                      ) : (
                        <Typography.Text type='secondary'>暂无影像结果，请先进入影像输入页面。</Typography.Text>
                      )}
                    </Space>
                  </div>
                  <div style={innerBlockStyle}>
                    <Space direction='vertical' size={6} style={{ width: '100%' }}>
                      <Typography.Text type='secondary'>多模态概要</Typography.Text>
                      <Tag color='default'>暂未接入</Tag>
                      <Typography.Text>临床与影像都初步具备后，再测试多模态评估。</Typography.Text>
                    </Space>
                  </div>
                </div>
                <Space wrap size={8}>
                  <Link href={'/cases/' + caseId + '/model-input'}>进入临床表格</Link>
                  <Link href={'/cases/' + caseId + '/imaging-inputs'}>进入影像输入</Link>
                  <Link href={'/cases/' + caseId + '/shadow-audit'}>进入审计溢源</Link>
                  <Link href={'/cases/' + caseId + '/lineage'}>进入 Trace / 源头</Link>
                </Space>
              </Space>
            ),
          },
          {
            key: 'inputs',
            label: '输入数据',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='info'
                  showIcon
                  message='输入数据分层管理'
                  description='表格特征与输入快照、影像输入 / 引用登记、缺失值确认都在这里汇总。先看输入，再谈模型评估。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>表格特征与输入快照</Typography.Text>
                      <Tag color={context.tableSnapshotCount > 0 ? 'green' : 'default'}>{context.tableSnapshotCount > 0 ? '已登记' : '待补齐'}</Tag>
                      <Typography.Text>CAP/COP 临床特征在这里查看输入映射和校验状态。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/model-input'}>进入表格输入</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>影像输入 / 引用登记</Typography.Text>
                      <Tag color={context.imagingInputCount > 0 ? 'green' : 'default'}>{context.imagingInputCount > 0 ? '已登记' : '待登记'}</Tag>
                      <Typography.Text>只登记影像 metadata / reference，不上传文件，不触发模型。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/imaging-inputs'}>进入影像输入</Link>
                    </Space>
                  </div>
                                    <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>DICOM preprocessing contract</Typography.Text>
                      <Tag color={context.imagingInputCount > 0 ? 'blue' : 'default'}>metadata-only</Tag>
                      <Typography.Text>DICOM series 先登记引用，再由 dcm2niix + N4 contract 转成 image.nii.gz；label.nii.gz 只用于训练/评估引用。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/imaging-inputs'}>查看 DICOM 预处理契约</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>缺失值确认</Typography.Text>
                      <Tag color='gold'>需要医生确认</Tag>
                      <Typography.Text>遇到 required feature 缺失时，走缺失值咨询或明确默认策略，不能 silent fallback。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/missing-consultation'}>进入缺失值确认</Link>
                    </Space>
                  </div>
                </div>
              </Space>
            ),
          },
          {
            key: 'models',
            label: '模型评估',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='warning'
                  showIcon
                  message='这里展示的是 shadow only 状态，不是诊断结论'
                  description='clinical MLP 仍保留 schema_unverified 风险；imaging ResNet18 仍是 prototype candidate；multimodal 还未接入。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>clinical MLP</Typography.Text>
                      <Space wrap size={6}>
                        <Tag color='orange'>tabular baseline</Tag>
                        <Tag color='orange'>schema_unverified</Tag>
                        <Tag>Shadow only</Tag>
                      </Space>
                      <Typography.Text>只用于 shadow 审计和医生复核，不要当作正式推荐。</Typography.Text>
                      {context.latestShadowRun
                        ? <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + latestShadowRunId}>查看临床 MLP 审计</Link>
                        : <Link href={'/cases/' + caseId + '/shadow-audit'}>查看 Shadow 审计</Link>}
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>imaging ResNet18</Typography.Text>
                      {context.latestImagingRun && context.latestImagingRun.status === 'shadow_success' && context.latestImagingOutput ? (
                        <>
                          <Space wrap size={6}>
                            <Tag color='green'>已完成受控 shadow</Tag>
                            <Tag color='gold'>synthetic-only</Tag>
                            <Tag color='gold'>coursework_mvp</Tag>
                            <Tag color='orange'>not_for_diagnosis</Tag>
                            <Tag color='blue'>prototype_state=real_shadow_executed</Tag>
                            {(context.latestImagingOutput.prediction_probability_json as Record<string, unknown> | undefined)?.calibrated === false ? <Tag color='orange'>概率未校准</Tag> : null}
                          </Space>
                          <Alert
                            type='warning'
                            showIcon
                            message='影像 ResNet18 旁路评估：已完成受控 shadow'
                            description='candidate_label、CAP/COP 概率、confidence 和 uncertainty 仅用于课程 shadow 演示，不代表诊断结论。'
                          />
                          <Descriptions bordered size='small' column={2}>
                            <Descriptions.Item label='旁路候选标签'>{getImagingCandidateSummary(context.latestImagingOutput.candidate_label)}</Descriptions.Item>
                            <Descriptions.Item label='概率 CAP'>{formatProbability(getProbability(extractProbabilityMap(context.latestImagingOutput.prediction_probability_json), 'CAP'))}</Descriptions.Item>
                            <Descriptions.Item label='概率 COP'>{formatProbability(getProbability(extractProbabilityMap(context.latestImagingOutput.prediction_probability_json), 'COP'))}</Descriptions.Item>
                            <Descriptions.Item label='置信度'>{getScalarValue(context.latestImagingOutput.confidence_json)}</Descriptions.Item>
                            <Descriptions.Item label='不确定性'>{getScalarValue(context.latestImagingOutput.uncertainty_json)}</Descriptions.Item>
                            <Descriptions.Item label='状态'>{getImagingStatusLabel(context.latestImagingRun.status)}</Descriptions.Item>
                            <Descriptions.Item label='原型状态'>{getImagingStatusLabel(context.latestImagingRun.prototype_state)}</Descriptions.Item>
                            <Descriptions.Item label='artifact_hash'>{context.latestImagingRun.artifact_hash || '-'}</Descriptions.Item>
                            <Descriptions.Item label='桥接入口'><Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + context.latestImagingRun.shadow_run_id}>查看影像 Shadow 审计</Link></Descriptions.Item>
                          </Descriptions>
                          <Card size='small' title='预处理摘要' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
                            {context.latestImagingOutput.preprocessing_summary ? renderJsonBlock(context.latestImagingOutput.preprocessing_summary) : <Typography.Text type='secondary'>暂无预处理摘要</Typography.Text>}
                          </Card>
                        </>
                      ) : context.latestImagingRun ? (
                        <>
                          <Space wrap size={6}>
                            <Tag color='gold'>artifact preflight</Tag>
                            <Tag color='gold'>runner prototype candidate</Tag>
                            <Tag>backend bridge stub</Tag>
                          </Space>
                          <Alert
                            type='warning'
                            showIcon
                            message='影像 ResNet18 旁路桥接：当前仍为关闭态 / 原型未执行'
                            description='shadow_disabled、imaging_runner_not_loaded、prototype_not_executed。当前仅保留桥接位置，不构成诊断或正式推荐。'
                          />
                          <Typography.Text>当前只保留原型与桥接位置，不把它包装成真实结果。</Typography.Text>
                          <Link href={'/cases/' + caseId + '/imaging-inputs'}>查看影像输入</Link>
                        </>
                      ) : (
                        <>
                          <Space wrap size={6}>
                            <Tag color='gold'>artifact preflight</Tag>
                            <Tag color='gold'>runner prototype candidate</Tag>
                            <Tag>backend bridge stub</Tag>
                          </Space>
                          <Typography.Text>当前只保留原型与桥接位置，不把它包装成真实结果。</Typography.Text>
                          <Link href={'/cases/' + caseId + '/imaging-inputs'}>查看影像输入</Link>
                        </>
                      )}
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>multimodal ResNet18</Typography.Text>
                      <Space wrap size={6}>
                        <Tag color='default'>待接入</Tag>
                        <Tag>Shadow only</Tag>
                      </Space>
                      <Typography.Text>多模态融合先保留位置，不在本阶段触发任何执行。</Typography.Text>
                    </Space>
                  </div>
                </div>
                <div style={{ marginTop: 12, border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff', width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
                  <Space direction='vertical' size={8} style={{ width: '100%' }}>
                    <Typography.Text type='secondary'>影像 ResNet18 旁路桥接</Typography.Text>
                    <Alert
                      type='warning'
                      showIcon
                      message='影像 ResNet18 旁路桥接：已接通原型 runner'
                      description='当前状态：未执行真实推理 / 原型未加载。shadow_disabled（Shadow 已禁用）/ imaging_runner_not_loaded（影像原型未加载）/ prototype_not_executed（原型未执行）。不用于诊断，不生成正式推荐，不写病例证据图。'
                    />
                    {context.latestImagingRun ? (
                      <Descriptions bordered size='small' column={2}>
                        <Descriptions.Item label='shadow_run_id'>{context.latestImagingRun.shadow_run_id}</Descriptions.Item>
                        <Descriptions.Item label='状态'>{getImagingStatusLabel(context.latestImagingRun.status)}</Descriptions.Item>
                        <Descriptions.Item label='error_code'>{getImagingStatusLabel(context.latestImagingRun.error_code)}</Descriptions.Item>
                        <Descriptions.Item label='prototype_state'>{getImagingStatusLabel(context.latestImagingRun.prototype_state)}</Descriptions.Item>
                        <Descriptions.Item label='artifact_hash'>{context.latestImagingRun.artifact_hash || '-'}</Descriptions.Item>
                        <Descriptions.Item label='started_at'>{context.latestImagingRun.started_at || '-'}</Descriptions.Item>
                        <Descriptions.Item label='created_at'>{context.latestImagingRun.created_at || '-'}</Descriptions.Item>
                        <Descriptions.Item label='桥接入口'>
                          <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + context.latestImagingRun.shadow_run_id}>查看影像 Shadow 审计</Link>
                        </Descriptions.Item>
                      </Descriptions>
                    ) : (
                      <Space direction='vertical' size={4}>
                        <Typography.Text>暂无影像 Shadow 审计记录。</Typography.Text>
                        <Typography.Text type='secondary'>影像桥接位置已预留在病例工作台，但当前病例还没有可展示的运行记录。</Typography.Text>
                        <Link href={'/cases/' + caseId + '/shadow-audit'}>前往影像 Shadow 审计</Link>
                      </Space>
                    )}
                  </Space>
                </div>
              </Space>
            ),
          },
          {
            key: 'twin',
            label: '数字孪生',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='info'
                  showIcon
                  message='病例级 lung-state twin 仅用于课程演示'
                  description='它显示输入状态、影像状态、模型状态和不确定性 / 限制，不是诊断图，也不是正式临床推荐。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>输入状态</Typography.Text>
                      <Typography.Text>{context.tableSnapshotCount > 0 ? '表格输入快照已建立' : '表格输入待建立'}</Typography.Text>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>影像状态</Typography.Text>
                      <Typography.Text>{context.imagingInputCount > 0 ? '影像 metadata / reference 已登记' : '影像输入待登记'}</Typography.Text>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>模型状态</Typography.Text>
                      <Typography.Text>{context.latestShadowRun ? '已有 Shadow 记录' : '仍是 Shadow only / prototype'}</Typography.Text>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>不确定性 / 限制</Typography.Text>
                      <Typography.Text>
                        {context.latestShadowOutput
                          ? '概率未校准、仅供复核'
                          : '当前仍是课程演示，不可当诊断'}
                      </Typography.Text>
                    </Space>
                  </div>
                </div>
                <Alert
                  type='info'
                  showIcon
                  message={context.latestImagingOutput?.candidate_label ? ('CAP/COP 影像旁路状态：' + getImagingCandidateSummary(context.latestImagingOutput.candidate_label)) : 'CAP/COP 影像旁路状态：待建立'}
                  description='仅供课程 shadow 演示，不代表诊断结论，需医生复核。'
                />
                <Alert
                  type='warning'
                  showIcon
                  message='课程演示标识'
                  description='Shadow only / not_for_diagnosis / not formal recommendation。病例级肺部状态 twin 只保留展示，不产生诊断结论。'
                />
              </Space>
            ),
          },
          {
            key: 'audit',
            label: '审计溯源',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='info'
                  showIcon
                  message='审计与溯源入口收口'
                  description='这里汇总 Shadow 审计、Trace / provenance 和访问审计的入口。技术字段只在详情或折叠区展示。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>Shadow 审计</Typography.Text>
                      <Typography.Text>查看旁路审计记录、候选标签和输出摘要。</Typography.Text>
                      <Link href={latestShadowRunId ? '/cases/' + caseId + '/shadow-audit?shadow_run_id=' + latestShadowRunId : '/cases/' + caseId + '/shadow-audit'}>进入 Shadow 审计</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>Trace / provenance</Typography.Text>
                      <Typography.Text>查看病例溯源与证据链入口，但不把 raw JSON 作为主视觉。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/lineage'}>进入 Trace / 溯源</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>Access audit</Typography.Text>
                      <Typography.Text>前端暂只保留工作台入口位，实际访问审计待接入。</Typography.Text>
                      <Tag>待接入</Tag>
                    </Space>
                  </div>
                </div>
              </Space>
            ),
          },
        ]}
      />
    </Space>
  );
}
