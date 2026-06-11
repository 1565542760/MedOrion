'use client';

import Link from 'next/link';
import axios from 'axios';
import { use, useEffect, useMemo, useState } from 'react';
import { Alert, Card, Collapse, Descriptions, Empty, Space, Spin, Table, Tag, Typography } from 'antd';
import { useSearchParams } from 'next/navigation';
import {
  getShadowInferenceRun,
  getShadowRunOutputs,
  listShadowRunsByCase,
  listShadowRunsByTrace,
  type ShadowInferenceRunItem,
  type ShadowInferenceRunOutputItem,
} from '@/lib/api';

type ShadowRow = ShadowInferenceRunItem;

type ProbabilityMap = Record<string, unknown>;

const LIMITATION_LABELS: Record<string, string> = {
  not_for_diagnosis: '非诊断',
  shadow_only: '旁路审计',
  not_formal_recommendation: '非正式推荐',
  not_externally_validated: '未经过外部验证',
  internal_retrospective_evaluation_only: '仅限内部回顾性评估',
  probability_uncalibrated: '概率未校准',
  extreme_probability_not_clinical_certainty: '极端概率不等于临床确定性',
  requires_doctor_review: '需要医生复核',
  requires_quality_review_before_clinical_use: '临床使用前需完成质控审查',
  bridge_runtime: '桥接运行时',
  long_term_runtime_target: '长期运行目标',
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function translateError(error: unknown) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const data = error.response?.data as { detail?: { code?: string; message?: string } | string; code?: string; message?: string } | undefined;
    const code = typeof data?.detail === 'string' ? data.detail : (data?.detail && typeof data.detail === 'object' ? data.detail.code : data?.code || data?.message || '');
    if (status === 404 || code === 'shadow_run_not_found') return 'shadow 审计记录未找到';
    if (status === 404 || code === 'shadow_output_not_found') return 'shadow 审计输出未找到';
    if (status === 422) return 'shadow 审计参数校验失败';
  }
  return 'shadow 审计加载失败';
}

function renderJson(value: unknown) {
  if (value === null || value === undefined) return '-';
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{text}</pre>;
}

function renderBoolTag(value?: boolean | null) {
  return value ? <Tag color='green'>是</Tag> : <Tag>否</Tag>;
}

function renderText(value?: string | number | null) {
  if (value === null || value === undefined || value === '') return '-';
  return value;
}

function formatDuration(value?: number | null) {
  if (typeof value !== 'number') return '-';
  return value + ' ms';
}

function formatProbability(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    const text = value.toFixed(3).replace(/\.?(?:0+)$/, '');
    return text === '' ? '0' : text;
  }
  if (typeof value === 'string' && value.trim() !== '') return value;
  return '-';
}

function extractLimitations(value: unknown) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item));
  }
  if (isRecord(value)) {
    const parts: string[] = [];
    for (const [key, item] of Object.entries(value)) {
      if (typeof item === 'boolean') {
        if (item) parts.push(key);
      } else if (typeof item === 'string') {
        parts.push(key + ': ' + item);
      } else if (typeof item === 'number') {
        parts.push(key + ': ' + String(item));
      } else if (Array.isArray(item)) {
        parts.push(...item.map((entry) => key + ': ' + String(entry)));
      }
    }
    return parts;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    return [value];
  }
  return [] as string[];
}

function limitationTagText(flag: string) {
  const normalized = flag.trim();
  if (normalized.includes(':')) {
    const [key, rest] = normalized.split(':', 2);
    const label = LIMITATION_LABELS[key.trim()] || key.trim();
    return rest.trim() ? label + ': ' + rest.trim() : label;
  }
  const label = LIMITATION_LABELS[normalized];
  return label || normalized;
}

function extractProbabilityMap(value: unknown): ProbabilityMap {
  if (isRecord(value)) return value;
  return {};
}

function getProbability(probabilities: ProbabilityMap, key: string) {
  const direct = probabilities[key];
  if (direct !== undefined) return direct;
  const lower = probabilities[key.toLowerCase()];
  if (lower !== undefined) return lower;
  const upper = probabilities[key.toUpperCase()];
  if (upper !== undefined) return upper;
  return null;
}

function getConfidenceInfo(value: unknown) {
  if (typeof value === 'number') {
    return { valueText: formatProbability(value), calibrated: null as boolean | null };
  }
  if (typeof value === 'string') {
    return { valueText: value, calibrated: null as boolean | null };
  }
  if (isRecord(value)) {
    const scalar = 'value' in value ? formatProbability(value.value) : JSON.stringify(value);
    const calibrated = typeof value.calibrated === 'boolean' ? value.calibrated : null;
    return { valueText: scalar, calibrated };
  }
  return { valueText: '-', calibrated: null as boolean | null };
}

function getRawLogits(value: unknown) {
  if (isRecord(value) && 'logits' in value) {
    return (value as Record<string, unknown>).logits;
  }
  return null;
}

function getPreprocessingSummary(value: unknown) {
  if (!isRecord(value)) return null;
  const summary = value.preprocessing_summary;
  return isRecord(summary) ? summary : null;
}

function isImagingBridgeRun(run: ShadowInferenceRunItem | null) {
  if (!run) return false;
  const haystack = [run.adapter_code, run.model_version_id, run.model_input_schema_id].filter(Boolean).join(' ').toLowerCase();
  return haystack.includes('imaging');
}

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const searchParams = useSearchParams();
  const traceId = searchParams.get('trace_id') || '';
  const focusShadowRunId = searchParams.get('shadow_run_id') || '';
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState('');
  const [runs, setRuns] = useState<ShadowRow[]>([]);
  const [outputsByRunId, setOutputsByRunId] = useState<Record<string, ShadowInferenceRunOutputItem[]>>({});
  const [outputErrorsByRunId, setOutputErrorsByRunId] = useState<Record<string, string>>({});
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const [focusRun, setFocusRun] = useState<ShadowRow | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setPageError('');
      setRuns([]);
      setOutputsByRunId({});
      setOutputErrorsByRunId({});
      setExpandedRowKeys([]);
      setFocusRun(null);

      try {
        const listResponse = traceId ? await listShadowRunsByTrace(traceId) : await listShadowRunsByCase(caseId);
        let nextRuns = listResponse.items || [];
        let nextFocus: ShadowRow | null = null;

        if (focusShadowRunId) {
          const run = await getShadowInferenceRun(focusShadowRunId);
          nextFocus = run;
          const exists = nextRuns.some((item) => item.shadow_run_id === run.shadow_run_id);
          if (!exists) {
            nextRuns = [run, ...nextRuns];
          }
        }

        if (!active) return;
        setRuns(nextRuns);
        setFocusRun(nextFocus);
        const shouldExpand = nextFocus ? [nextFocus.shadow_run_id] : (nextRuns.length === 1 ? [nextRuns[0].shadow_run_id] : []);
        setExpandedRowKeys(shouldExpand);

        const outputPairs = await Promise.all(
          nextRuns.map(async (run) => {
            try {
              const data = await getShadowRunOutputs(run.shadow_run_id);
              return [run.shadow_run_id, data.items || [], ''] as const;
            } catch (error) {
              return [run.shadow_run_id, [], translateError(error)] as const;
            }
          })
        );

        if (!active) return;
        setOutputsByRunId(Object.fromEntries(outputPairs.map(([runId, items]) => [runId, items])) as Record<string, ShadowInferenceRunOutputItem[]>);
        setOutputErrorsByRunId(Object.fromEntries(outputPairs.filter(([, , error]) => !!error).map(([runId, , error]) => [runId, error])) as Record<string, string>);
      } catch (error) {
        if (!active) return;
        setPageError(translateError(error));
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [caseId, traceId, focusShadowRunId]);

  const filteredRuns = useMemo(() => {
    if (!traceId) return runs;
    return runs.filter((run) => run.trace_id === traceId);
  }, [runs, traceId]);

  const featuredRun = useMemo(() => {
    if (focusRun) return focusRun;
    return filteredRuns[0] || null;
  }, [focusRun, filteredRuns]);

  const featuredOutput = useMemo(() => {
    if (!featuredRun) return null;
    return outputsByRunId[featuredRun.shadow_run_id]?.[0] || null;
  }, [featuredRun, outputsByRunId]);

  const imagingRuns = useMemo(() => filteredRuns.filter(isImagingBridgeRun), [filteredRuns]);
  const featuredImagingRun = useMemo(() => {
    if (focusRun && isImagingBridgeRun(focusRun)) return focusRun;
    return imagingRuns[0] || null;
  }, [focusRun, imagingRuns]);
  const featuredImagingOutput = useMemo(() => {
    if (!featuredImagingRun) return null;
    return outputsByRunId[featuredImagingRun.shadow_run_id]?.[0] || null;
  }, [featuredImagingRun, outputsByRunId]);

  const probabilityMap = useMemo(() => extractProbabilityMap(featuredOutput?.prediction_probability_json), [featuredOutput]);
  const limitationFlags = useMemo(() => extractLimitations(featuredOutput?.limitations_json), [featuredOutput]);
  const confidenceInfo = useMemo(() => getConfidenceInfo(featuredOutput?.confidence_json), [featuredOutput]);
  const rawLogits = useMemo(() => getRawLogits(featuredOutput?.prediction_raw_json), [featuredOutput]);
    const imagingProbabilityMap = useMemo(() => extractProbabilityMap(featuredImagingOutput?.prediction_probability_json), [featuredImagingOutput]);
  const imagingConfidenceInfo = useMemo(() => getConfidenceInfo(featuredImagingOutput?.confidence_json), [featuredImagingOutput]);
    const imagingRawLogits = useMemo(() => getRawLogits(featuredImagingOutput?.prediction_raw_json), [featuredImagingOutput]);
    const imagingPreprocessingSummary = useMemo(() => getPreprocessingSummary(featuredImagingOutput?.prediction_raw_json), [featuredImagingOutput]);
    const imagingProbabilityUncalibrated = imagingProbabilityMap && (imagingProbabilityMap.calibrated === false || imagingConfidenceInfo.calibrated === false);
    const imagingIsSuccess = Boolean(featuredImagingRun && featuredImagingRun.status === 'shadow_success' && featuredImagingOutput);
    const imagingOutput = featuredImagingOutput;
  const probabilityUncalibrated = limitationFlags.some((flag) => flag === 'probability_uncalibrated') || confidenceInfo.calibrated === false;
  const extremeProbabilityWarning = limitationFlags.some((flag) => flag === 'extreme_probability_not_clinical_certainty');
  const notExternallyValidated = limitationFlags.some((flag) => flag === 'not_externally_validated');
  const requiresDoctorReview = limitationFlags.some((flag) => flag === 'requires_doctor_review');
  const requiresQualityReview = limitationFlags.some((flag) => flag === 'requires_quality_review_before_clinical_use');

  const columns = [
    { title: 'shadow_run_id', dataIndex: 'shadow_run_id' },
    { title: 'trace_id', dataIndex: 'trace_id' },
    { title: 'model_version_id', dataIndex: 'model_version_id' },
    { title: 'artifact_hash', dataIndex: 'artifact_hash', render: (value: string | null | undefined) => renderText(value) },
    { title: 'adapter_code', dataIndex: 'adapter_code', render: (value: string | null | undefined) => renderText(value) },
    { title: 'status', dataIndex: 'status', render: (value: string | null | undefined) => renderText(value) },
    { title: 'prototype_state', dataIndex: 'prototype_state', render: (value: string | null | undefined) => renderText(value) },
    { title: 'runtime_stub', dataIndex: 'runtime_stub', render: (value: boolean | null | undefined) => renderBoolTag(value) },
    { title: 'not_for_diagnosis', dataIndex: 'not_for_diagnosis', render: (value: boolean | null | undefined) => renderBoolTag(value) },
    { title: 'started_at', dataIndex: 'started_at', render: (value: string | null | undefined) => renderText(value) },
    { title: 'duration_ms', dataIndex: 'duration_ms', render: (value: number | null | undefined) => formatDuration(value) },
    { title: 'error_code', dataIndex: 'error_code', render: (value: string | null | undefined) => renderText(value) },
  ];

  return (
    <div style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>Shadow 审计查看</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}{traceId ? ' · Trace / 溯源 ID：' + traceId : ''}</Typography.Text>

      <Alert
        type='info'
        showIcon
        message='shadow audit 是旁路审计'
        description='它不影响正式 recommendation，不是诊断结论，也不是医生替代。当前示例记录仅用于测试和开发；运行模式为测试桩（runtime_stub=true），表示不是正式真实推理。'
      />
      <Alert
        type='warning'
        showIcon
        message='字段契约待复核 / schema_unverified'
        description='该结果来自尚未完全确认的前端输入 schema，不能作为可靠评估。当前 36 个前端输入字段尚未确认等同于 fold5 真实训练输入，CAP/COP 原表与当前输入 schema 存在字段差异，Sex 等字段编码未验证。'
        style={{ marginTop: 12 }}
      />

        {featuredImagingRun ? (
          <Card title='影像 ResNet18 旁路桥接状态' size='small'>
            <Space direction='vertical' size={8} style={{ width: '100%' }}>
              {imagingIsSuccess ? (
                <>
                  <Space wrap size={6}>
                    <Tag color='green'>已完成受控 shadow</Tag>
                    <Tag color='gold'>synthetic-only</Tag>
                    <Tag color='gold'>coursework_mvp</Tag>
                    <Tag color='orange'>not_for_diagnosis</Tag>
                    <Tag color='blue'>prototype_state=real_shadow_executed</Tag>
                    {imagingProbabilityUncalibrated ? <Tag color='orange'>概率未校准</Tag> : null}
                  </Space>
                  <Alert
                    type='warning'
                    showIcon
                    message='影像 ResNet18 旁路评估：已完成受控 shadow'
                    description='candidate_label、CAP/COP 概率、confidence 和 uncertainty 仅用于课程 shadow 演示，不代表诊断结论。'
                  />
                  <Descriptions bordered size='small' column={2}>
                    <Descriptions.Item label='shadow_run_id'>{featuredImagingRun.shadow_run_id || '-'}</Descriptions.Item>
                    <Descriptions.Item label='旁路候选标签'>{renderText(imagingOutput?.candidate_label)}</Descriptions.Item>
                    <Descriptions.Item label='概率输出 CAP'>{formatProbability(getProbability(imagingProbabilityMap, 'CAP'))}</Descriptions.Item>
                    <Descriptions.Item label='概率输出 COP'>{formatProbability(getProbability(imagingProbabilityMap, 'COP'))}</Descriptions.Item>
                    <Descriptions.Item label='置信度'>{imagingConfidenceInfo.valueText}</Descriptions.Item>
                    <Descriptions.Item label='不确定性'>{renderJson(imagingOutput?.uncertainty_json)}</Descriptions.Item>
                    <Descriptions.Item label='状态'>{renderText(featuredImagingRun.status)}</Descriptions.Item>
                    <Descriptions.Item label='prototype_state'>{renderText(featuredImagingRun.prototype_state)}</Descriptions.Item>
                    <Descriptions.Item label='artifact_hash'>{renderText(featuredImagingRun.artifact_hash)}</Descriptions.Item>
                    <Descriptions.Item label='started_at'>{renderText(featuredImagingRun.started_at)}</Descriptions.Item>
                    <Descriptions.Item label='created_at'>{renderText(featuredImagingRun.created_at)}</Descriptions.Item>
                    <Descriptions.Item label='桥接入口'>
                      <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + featuredImagingRun.shadow_run_id}>查看影像 Shadow 审计</Link>
                    </Descriptions.Item>
                  </Descriptions>
                  <Card size='small' title='预处理摘要' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
                    {imagingPreprocessingSummary ? renderJson(imagingPreprocessingSummary) : <Typography.Text type='secondary'>暂无预处理摘要</Typography.Text>}
                  </Card>
                  {imagingRawLogits ? (
                    <Collapse
                      size='small'
                      items={[
                        {
                          key: 'raw-imaging-output',
                          label: '原始影像输出（raw logits）',
                          children: (
                            <Space direction='vertical' size={8} style={{ width: '100%' }}>
                              <Typography.Text type='secondary'>原始影像输出仅用于 shadow 审计和技术复核，不作为临床结论主体。</Typography.Text>
                              <Card size='small' title='logits（技术复核）'>
                                {renderJson(imagingRawLogits)}
                              </Card>
                              <Card size='small' title='prediction_raw_json（技术复核）'>
                                {renderJson(imagingOutput?.prediction_raw_json)}
                              </Card>
                            </Space>
                          ),
                        },
                      ]}
                    />
                  ) : null}
                </>
              ) : (
                <>
                  <Alert
                    type='warning'
                    showIcon
                    message='影像 ResNet18 旁路桥接：已接通原型 runner'
                    description='当前状态：未执行真实推理 / 原型未加载。shadow_disabled（Shadow 已禁用）/ imaging_runner_not_loaded（影像原型未加载）/ prototype_not_executed（原型未执行）。不用于诊断，不生成正式推荐，不写病例证据图。'
                  />
                  <Descriptions bordered size='small' column={2}>
                    <Descriptions.Item label='shadow_run_id'>{featuredImagingRun.shadow_run_id || '-'}</Descriptions.Item>
                    <Descriptions.Item label='状态'>{renderText(featuredImagingRun.status)}</Descriptions.Item>
                    <Descriptions.Item label='error_code'>{renderText(featuredImagingRun.error_code)}</Descriptions.Item>
                    <Descriptions.Item label='prototype_state'>{renderText(featuredImagingRun.prototype_state)}</Descriptions.Item>
                    <Descriptions.Item label='artifact_hash'>{renderText(featuredImagingRun.artifact_hash)}</Descriptions.Item>
                    <Descriptions.Item label='started_at'>{renderText(featuredImagingRun.started_at)}</Descriptions.Item>
                    <Descriptions.Item label='created_at'>{renderText(featuredImagingRun.created_at)}</Descriptions.Item>
                    <Descriptions.Item label='桥接入口'>
                      <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + featuredImagingRun.shadow_run_id}>查看影像 Shadow 审计</Link>
                    </Descriptions.Item>
                  </Descriptions>
                </>
              )}
            </Space>
          </Card>
        ) : null}

      <Card title='入口说明' extra={<Link href={'/cases/' + caseId + '/small-models'}>返回小模型分析</Link>}>
        <Space direction='vertical' size={8}>
          <Typography.Text>先在病例工作流里选择病例，再查看 shadow 审计记录。</Typography.Text>
          <Typography.Text>如果需要按 trace 过滤，可通过 trace_id 参数进入本页。</Typography.Text>
          <Typography.Text>shadow audit 只读展示，不写入，也不执行模型。</Typography.Text>
        </Space>
      </Card>

      <Card title='临床 MLP CAP/COP Shadow 结果'>
        {featuredOutput ? (
          <Space direction='vertical' size={12} style={{ width: '100%' }}>
            <Space wrap size={8}>
              <Tag color='orange'>schema_unverified</Tag>
              <Tag color='gold'>旁路审计</Tag>
              <Tag color='volcano'>非诊断</Tag>
              <Tag color='blue'>非正式推荐</Tag>
              <Tag color='geekblue'>需要医生复核</Tag>
              <Tag color='purple'>临床使用前需完成质控审查</Tag>
            </Space>

            <Alert
              type='warning'
              showIcon
              message='仅供 shadow 审计和医生复核参考'
              description={
                <Space direction='vertical' size={2}>
                  <Typography.Text>这是旁路审计结果，不影响正式 recommendation，不是诊断结论，也不是医生替代。</Typography.Text>
                  <Typography.Text>当前示例记录用于测试/开发；运行模式为测试桩（runtime_stub=true），表示不是正式真实推理。</Typography.Text>
                </Space>
              }
            />

            {probabilityUncalibrated || extremeProbabilityWarning || notExternallyValidated || requiresDoctorReview || requiresQualityReview ? (
              <Alert
                type='warning'
                showIcon
                message='概率与临床使用警示'
                description={
                  <Space direction='vertical' size={2}>
                    {probabilityUncalibrated ? <Typography.Text>概率未校准。</Typography.Text> : null}
                    {extremeProbabilityWarning ? <Typography.Text>极端概率不等于临床确定性。</Typography.Text> : null}
                    {notExternallyValidated ? <Typography.Text>该输出未经过外部验证。</Typography.Text> : null}
                    <Typography.Text>仅供 shadow 审计和医生复核参考。</Typography.Text>
                    {requiresDoctorReview ? <Typography.Text>需要医生复核。</Typography.Text> : null}
                    {requiresQualityReview ? <Typography.Text>需要在临床使用前完成质控审查。</Typography.Text> : null}
                  </Space>
                }
              />
            ) : null}

            <Descriptions bordered size='small' column={2}>
              <Descriptions.Item label='旁路候选标签'>{renderText(featuredOutput.candidate_label)}</Descriptions.Item>
              <Descriptions.Item label='概率输出 CAP'>{formatProbability(getProbability(probabilityMap, 'CAP'))}</Descriptions.Item>
              <Descriptions.Item label='概率输出 COP'>{formatProbability(getProbability(probabilityMap, 'COP'))}</Descriptions.Item>
              <Descriptions.Item label='置信度'>{confidenceInfo.valueText}</Descriptions.Item>
              <Descriptions.Item label='不确定性'>{renderJson(featuredOutput.uncertainty_json)}</Descriptions.Item>
              <Descriptions.Item label='模型版本 ID'>{renderText(featuredRun.model_version_id)}</Descriptions.Item>
              <Descriptions.Item label='输入快照 ID'>{renderText(featuredRun.input_snapshot_id)}</Descriptions.Item>
              <Descriptions.Item label='制品哈希'>{renderText(featuredRun.artifact_hash)}</Descriptions.Item>
              <Descriptions.Item label='适配器代码'>{renderText(featuredRun.adapter_code)}</Descriptions.Item>
              <Descriptions.Item label='状态'>{renderText(featuredRun.status)}</Descriptions.Item>
              <Descriptions.Item label='开始时间'>{renderText(featuredRun.started_at)}</Descriptions.Item>
              <Descriptions.Item label='创建时间'>{renderText(featuredRun.created_at)}</Descriptions.Item>
            </Descriptions>

            <Card size='small' title='限制说明 / 告警'>
              {limitationFlags.length === 0 ? (
                <Empty description='暂无限制信息' />
              ) : (
                <Space wrap size={8}>
                  {limitationFlags.map((flag) => (
                    <Tag key={flag} color='red'>
                      {limitationTagText(flag)}
                    </Tag>
                  ))}
                </Space>
              )}
            </Card>

            {rawLogits ? (
              <Collapse
                size='small'
                items={[
                  {
                    key: 'raw-model-output',
                    label: '原始模型输出（raw logits）',
                    children: (
                      <Space direction='vertical' size={8} style={{ width: '100%' }}>
                        <Typography.Text type='secondary'>原始模型输出，仅用于 shadow 审计，不作为主视觉或临床结论。</Typography.Text>
                        <Card size='small' title='logits（技术复核）'>
                          {renderJson(rawLogits)}
                        </Card>
                        <Card size='small' title='prediction_raw_json（技术复核）'>
                          {renderJson(featuredOutput.prediction_raw_json)}
                        </Card>
                      </Space>
                    ),
                  },
                ]}
              />
            ) : null}
          </Space>
        ) : (
          <Empty description='暂无 clinical MLP shadow 结果' />
        )}
      </Card>

      {pageError ? <Alert type='error' showIcon message={pageError} description='请检查 shadow_run_id 或 trace_id。' /> : null}

      <Card title='Shadow 审计记录列表'>
        <Spin spinning={loading}>
          {filteredRuns.length === 0 && !pageError ? (
            <Empty description='暂无 shadow 审计记录' />
          ) : (
            <Table
              rowKey='shadow_run_id'
              pagination={false}
              expandable={{
                expandedRowKeys,
                onExpandedRowsChange: (keys) => setExpandedRowKeys(keys.map((key) => String(key))),
                expandedRowRender: (run) => {
                  const outputs = outputsByRunId[run.shadow_run_id] || [];
                  const outputError = outputErrorsByRunId[run.shadow_run_id] || '';
                  return (
                    <Space direction='vertical' size={12} style={{ width: '100%' }}>
                      <Descriptions bordered size='small' column={2}>
                      <Descriptions.Item label='Shadow 记录 ID'>{run.shadow_run_id}</Descriptions.Item>
                      <Descriptions.Item label='Trace / 溯源 ID'>{run.trace_id}</Descriptions.Item>
                      <Descriptions.Item label='模型版本 ID'>{run.model_version_id}</Descriptions.Item>
                      <Descriptions.Item label='制品哈希'>{renderText(run.artifact_hash)}</Descriptions.Item>
                      <Descriptions.Item label='适配器代码'>{renderText(run.adapter_code)}</Descriptions.Item>
                      <Descriptions.Item label='状态'>{renderText(run.status)}</Descriptions.Item>
                      <Descriptions.Item label='原型状态'>{renderText(run.prototype_state)}</Descriptions.Item>
                      <Descriptions.Item label='运行模式'>{renderBoolTag(run.runtime_stub)}</Descriptions.Item>
                      <Descriptions.Item label='非诊断'>{renderBoolTag(run.not_for_diagnosis)}</Descriptions.Item>
                      <Descriptions.Item label='开始时间'>{renderText(run.started_at)}</Descriptions.Item>
                      <Descriptions.Item label='耗时（ms）'>{formatDuration(run.duration_ms)}</Descriptions.Item>
                      <Descriptions.Item label='错误码'>{renderText(run.error_code)}</Descriptions.Item>
                      <Descriptions.Item label='完成时间'>{renderText(run.completed_at)}</Descriptions.Item>
                    </Descriptions>
                      <Card title='输出展开区' size='small' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
                        {outputError ? <Alert type='error' showIcon message={outputError} /> : null}
                        {outputs.length === 0 ? (
                          <Empty description='暂无 clinical MLP shadow 结果' />
                        ) : (
                          <Table
                            size='small'
                            rowKey='output_id'
                            pagination={false}
                            dataSource={outputs}
                            scroll={{ x: 'max-content' }}
                            columns={[
                              { title: '旁路候选标签', dataIndex: 'candidate_label', render: (value: string | null | undefined) => renderText(value) },
                              { title: '概率输出', dataIndex: 'prediction_probability_json', render: (value: unknown) => renderJson(value) },
                              { title: '置信度', dataIndex: 'confidence_json', render: (value: unknown) => renderJson(value) },
                                { title: '不确定性', dataIndex: 'uncertainty_json', render: (value: unknown) => renderJson(value) },
                                { title: '限制说明', dataIndex: 'limitations_json', render: (value: unknown) => renderJson(value) },
                                { title: '输入质量标记', dataIndex: 'input_quality_flags_json', render: (value: unknown) => renderJson(value) },
                                { title: '预处理摘要', dataIndex: 'preprocessing_summary', render: (value: unknown) => renderJson(value) },
                              ]}
                            />
                        )}
                      </Card>
                    </Space>
                  );
                },
              }}
              dataSource={filteredRuns}
              columns={columns}
            />
          )}
        </Spin>
      </Card>

      {focusRun ? (
        <Card title='聚焦记录' extra={<Tag color='blue'>运行模式={String(focusRun.runtime_stub ?? false)}</Tag>}>
          <Descriptions bordered size='small' column={3}>
            <Descriptions.Item label='Shadow 记录 ID'>{focusRun.shadow_run_id}</Descriptions.Item>
            <Descriptions.Item label='Trace / 溯源 ID'>{focusRun.trace_id}</Descriptions.Item>
            <Descriptions.Item label='状态'>{focusRun.status || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>
      ) : null}
      </Space>
    </div>
  );
}

