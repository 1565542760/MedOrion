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
  not_for_diagnosis: 'Not for diagnosis',
  shadow_only: 'Shadow only',
  not_formal_recommendation: 'Not a formal recommendation',
  not_externally_validated: 'Not externally validated',
  internal_retrospective_evaluation_only: 'Internal retrospective evaluation only',
  probability_uncalibrated: '概率未校准',
  extreme_probability_not_clinical_certainty: '极端概率不等于临床确定性',
  requires_doctor_review: 'Requires doctor review',
  requires_quality_review_before_clinical_use: 'Requires quality review before clinical use',
  bridge_runtime: 'Bridge runtime',
  long_term_runtime_target: 'Long-term runtime target',
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
  if (Array.isArray(value)) return value.map((item) => String(item));
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
  if (typeof value === 'string' && value.trim() !== '') return [value];
  return [] as string[];
}

function limitationTagText(flag: string) {
  const normalized = flag.trim();
  if (normalized.includes(':')) {
    const [key, rest] = normalized.split(':', 2);
    const label = LIMITATION_LABELS[key.trim()] || key.trim();
    return rest.trim() ? label + ': ' + rest.trim() : label;
  }
  return LIMITATION_LABELS[normalized] || normalized;
}

function extractProbabilityMap(value: unknown): ProbabilityMap {
  return isRecord(value) ? value : {};
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

function renderProbabilityTag(label: string, value: unknown) {
  const text = formatProbability(value);
  return (
    <Tag color='default' style={{ marginInlineEnd: 0 }}>
      {label}: {text}
    </Tag>
  );
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

        const outputPairs = await Promise.all(nextRuns.map(async (run) => {
          try {
            const data = await getShadowRunOutputs(run.shadow_run_id);
            return [run.shadow_run_id, data.items || [], ''] as const;
          } catch (error) {
            return [run.shadow_run_id, [], translateError(error)] as const;
          }
        }));

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

  const featuredRun = useMemo(() => focusRun || filteredRuns[0] || null, [focusRun, filteredRuns]);

  const featuredOutput = useMemo(() => {
    if (!featuredRun) return null;
    return outputsByRunId[featuredRun.shadow_run_id]?.[0] || null;
  }, [featuredRun, outputsByRunId]);

  const probabilityMap = useMemo(() => extractProbabilityMap(featuredOutput?.prediction_probability_json), [featuredOutput]);
  const limitationFlags = useMemo(() => extractLimitations(featuredOutput?.limitations_json), [featuredOutput]);
  const confidenceInfo = useMemo(() => getConfidenceInfo(featuredOutput?.confidence_json), [featuredOutput]);
  const rawLogits = useMemo(() => getRawLogits(featuredOutput?.prediction_raw_json), [featuredOutput]);
  const probabilityUncalibrated = limitationFlags.some((flag) => flag === 'probability_uncalibrated') || confidenceInfo.calibrated === false;
  const extremeProbabilityWarning = limitationFlags.some((flag) => flag === 'extreme_probability_not_clinical_certainty');
  const notExternallyValidated = limitationFlags.some((flag) => flag === 'not_externally_validated');
  const requiresDoctorReview = limitationFlags.some((flag) => flag === 'requires_doctor_review');
  const requiresQualityReview = limitationFlags.some((flag) => flag === 'requires_quality_review_before_clinical_use');
  const extraSafetyNotes = [
    notExternallyValidated ? '该输出未经过外部验证。' : null,
    requiresDoctorReview ? '需要医生复核。' : null,
    requiresQualityReview ? '需要在临床使用前完成质控审查。' : null,
  ].filter(Boolean) as string[];

  const columns = [
    { title: 'shadow_run_id', dataIndex: 'shadow_run_id' },
    { title: 'trace_id', dataIndex: 'trace_id' },
    { title: 'model_version_id', dataIndex: 'model_version_id' },
    { title: 'artifact_hash', dataIndex: 'artifact_hash', render: (value: string | null | undefined) => renderText(value) },
    { title: 'adapter_code', dataIndex: 'adapter_code', render: (value: string | null | undefined) => renderText(value) },
    { title: 'status', dataIndex: 'status', render: (value: string | null | undefined) => renderText(value) },
    { title: 'runtime_stub', dataIndex: 'runtime_stub', render: (value: boolean | null | undefined) => renderBoolTag(value) },
    { title: 'not_for_diagnosis', dataIndex: 'not_for_diagnosis', render: (value: boolean | null | undefined) => renderBoolTag(value) },
    { title: 'started_at', dataIndex: 'started_at', render: (value: string | null | undefined) => renderText(value) },
    { title: 'duration_ms', dataIndex: 'duration_ms', render: (value: number | null | undefined) => formatDuration(value) },
    { title: 'error_code', dataIndex: 'error_code', render: (value: string | null | undefined) => renderText(value) },
  ];

  const provenanceItems = [
    { label: 'shadow_run_id', value: featuredRun?.shadow_run_id },
    { label: 'output_id', value: featuredOutput?.output_id },
    { label: 'model_version_id', value: featuredRun?.model_version_id },
    { label: 'input_snapshot_id', value: featuredRun?.input_snapshot_id },
    { label: 'artifact_hash', value: featuredRun?.artifact_hash },
    { label: 'adapter_code', value: featuredRun?.adapter_code },
    { label: 'status', value: featuredRun?.status },
    { label: 'started_at', value: featuredRun?.started_at },
    { label: 'created_at', value: featuredRun?.created_at },
  ];

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>Shadow 审计查看</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}{traceId ? ' · trace_id：' + traceId : ''}</Typography.Text>

      <Alert
        type='warning'
        showIcon
        message='shadow audit 是旁路审计'
        description='它不影响正式 recommendation，不是诊断结论，也不是医生替代。当前 dev record 仅用于测试和开发；runtime_stub=true 表示不是正式真实推理。'
      />

      <Card title='入口说明' extra={<Link href={'/cases/' + caseId + '/small-models'}>返回小模型分析</Link>}>
        <Space direction='vertical' size={8}>
          <Typography.Text>先在病例工作流里选择病例，再查看 shadow 审计记录。</Typography.Text>
          <Typography.Text>如果需要按 trace 过滤，可通过 trace_id 参数进入本页。</Typography.Text>
          <Typography.Text>shadow audit 只读展示，不写入，也不执行模型。</Typography.Text>
        </Space>
      </Card>

      <Card title='Clinical MLP CAP/COP Shadow Result'>
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Alert
            type='warning'
            showIcon
            message='安全警示'
            description={
              <Space direction='vertical' size={2}>
                <Typography.Text>Shadow only</Typography.Text>
                <Typography.Text>Not for diagnosis</Typography.Text>
                <Typography.Text>Not a formal recommendation</Typography.Text>
                <Typography.Text>Probability is uncalibrated</Typography.Text>
                <Typography.Text>Extreme probability is not clinical certainty</Typography.Text>
                <Typography.Text>Not externally validated</Typography.Text>
                <Typography.Text>Requires doctor review</Typography.Text>
                <Typography.Text>Requires quality review before clinical use</Typography.Text>
              </Space>
            }
          />

          {featuredOutput ? (
            <Space direction='vertical' size={12} style={{ width: '100%' }}>
              <Card size='small' title='模型旁路候选标签' styles={{ body: { paddingTop: 12 } }}>
                <Space direction='vertical' size={8} style={{ width: '100%' }}>
                  <Typography.Text type='secondary'>Shadow candidate label</Typography.Text>
                  <Tag color='gold' style={{ marginInlineEnd: 0 }}>{renderText(featuredOutput.candidate_label)}</Tag>
                  <Typography.Text type='secondary'>候选标签仅用于旁路审计参考，不是诊断结论，也不是正式推荐。</Typography.Text>
                </Space>
              </Card>

              <Descriptions bordered size='small' column={2}>
                <Descriptions.Item label='probabilities CAP'>
                  <Space size={8} wrap>
                    {renderProbabilityTag('CAP', getProbability(probabilityMap, 'CAP'))}
                    {probabilityUncalibrated ? <Tag color='orange'>未校准</Tag> : null}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label='probabilities COP'>
                  <Space size={8} wrap>
                    {renderProbabilityTag('COP', getProbability(probabilityMap, 'COP'))}
                    {probabilityUncalibrated ? <Tag color='orange'>未校准</Tag> : null}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label='confidence'>
                  <Space direction='vertical' size={4}>
                    <Typography.Text>{confidenceInfo.valueText}</Typography.Text>
                    {probabilityUncalibrated ? <Typography.Text type='danger'>概率未校准</Typography.Text> : null}
                    {extremeProbabilityWarning ? <Typography.Text type='danger'>极端概率不等于临床确定性</Typography.Text> : null}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label='uncertainty'>{renderJson(featuredOutput.uncertainty_json)}</Descriptions.Item>
                <Descriptions.Item label='model_version_id'>{renderText(featuredRun?.model_version_id)}</Descriptions.Item>
                <Descriptions.Item label='input_snapshot_id'>{renderText(featuredRun?.input_snapshot_id)}</Descriptions.Item>
                <Descriptions.Item label='artifact_hash'>{renderText(featuredRun?.artifact_hash)}</Descriptions.Item>
                <Descriptions.Item label='adapter_code'>{renderText(featuredRun?.adapter_code)}</Descriptions.Item>
                <Descriptions.Item label='status'>{renderText(featuredRun?.status)}</Descriptions.Item>
                <Descriptions.Item label='started_at'>{renderText(featuredRun?.started_at)}</Descriptions.Item>
                <Descriptions.Item label='created_at'>{renderText(featuredRun?.created_at)}</Descriptions.Item>
              </Descriptions>

              <Alert
                type='info'
                showIcon
                message='技术复核提示'
                description='当前输出仅供 shadow 审计和医生复核参考，不作为临床解释主体；请结合病例上下文与医生判断。'
              />

              {extraSafetyNotes.length > 0 ? (
                <Alert
                  type='warning'
                  showIcon
                  message='补充安全说明'
                  description={
                    <Space direction='vertical' size={2}>
                      {extraSafetyNotes.map((note) => (
                        <Typography.Text key={note}>{note}</Typography.Text>
                      ))}
                    </Space>
                  }
                />
              ) : null}

              <Card size='small' title='shadow audit context'>
                <Descriptions bordered size='small' column={2}>
                  {provenanceItems.map((item) => (
                    <Descriptions.Item key={item.label} label={item.label}>
                      {renderText(item.value)}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </Card>

              <Card size='small' title='limitations / warnings'>
                {limitationFlags.length === 0 ? (
                  <Empty description='暂无限制信息' />
                ) : (
                  <Space wrap size={8}>
                    {limitationFlags.map((flag) => (
                      <Tag key={flag} color='red'>{limitationTagText(flag)}</Tag>
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
                      label: 'Raw model output / raw logits',
                      children: (
                        <Space direction='vertical' size={8} style={{ width: '100%' }}>
                          <Typography.Text type='secondary'>原始模型输出，仅用于审计/技术复核，不是临床解释主体。</Typography.Text>
                          <Card size='small' title='logits'>
                            {renderJson(rawLogits)}
                          </Card>
                          <Card size='small' title='prediction_raw_json'>
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
        </Space>
      </Card>

      {pageError ? <Alert type='error' showIcon message={pageError} description='请检查 shadow_run_id 或 trace_id。' /> : null}

      <Card title='shadow run 列表'>
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
                        <Descriptions.Item label='shadow_run_id'>{run.shadow_run_id}</Descriptions.Item>
                        <Descriptions.Item label='trace_id'>{run.trace_id}</Descriptions.Item>
                        <Descriptions.Item label='model_version_id'>{run.model_version_id}</Descriptions.Item>
                        <Descriptions.Item label='artifact_hash'>{renderText(run.artifact_hash)}</Descriptions.Item>
                        <Descriptions.Item label='adapter_code'>{renderText(run.adapter_code)}</Descriptions.Item>
                        <Descriptions.Item label='status'>{renderText(run.status)}</Descriptions.Item>
                        <Descriptions.Item label='runtime_stub'>{renderBoolTag(run.runtime_stub)}</Descriptions.Item>
                        <Descriptions.Item label='not_for_diagnosis'>{renderBoolTag(run.not_for_diagnosis)}</Descriptions.Item>
                        <Descriptions.Item label='started_at'>{renderText(run.started_at)}</Descriptions.Item>
                        <Descriptions.Item label='duration_ms'>{formatDuration(run.duration_ms)}</Descriptions.Item>
                        <Descriptions.Item label='error_code'>{renderText(run.error_code)}</Descriptions.Item>
                        <Descriptions.Item label='completed_at'>{renderText(run.completed_at)}</Descriptions.Item>
                      </Descriptions>
                      <Card title='outputs 展开区' size='small'>
                        {outputError ? <Alert type='error' showIcon message={outputError} /> : null}
                        {outputs.length === 0 ? (
                          <Empty description='暂无 clinical MLP shadow 结果' />
                        ) : (
                          <Table
                            size='small'
                            rowKey='output_id'
                            pagination={false}
                            dataSource={outputs}
                            columns={[
                              { title: 'candidate_label', dataIndex: 'candidate_label', render: (value: string | null | undefined) => renderText(value) },
                              { title: 'prediction_probability_json', dataIndex: 'prediction_probability_json', render: (value: unknown) => renderJson(value) },
                              { title: 'confidence_json', dataIndex: 'confidence_json', render: (value: unknown) => renderJson(value) },
                              { title: 'uncertainty_json', dataIndex: 'uncertainty_json', render: (value: unknown) => renderJson(value) },
                              { title: 'limitations_json', dataIndex: 'limitations_json', render: (value: unknown) => renderJson(value) },
                              { title: 'input_quality_flags_json', dataIndex: 'input_quality_flags_json', render: (value: unknown) => renderJson(value) },
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
        <Card title='聚焦记录' extra={<Tag color='blue'>runtime_stub={String(focusRun.runtime_stub ?? false)}</Tag>}>
          <Descriptions bordered size='small' column={3}>
            <Descriptions.Item label='shadow_run_id'>{focusRun.shadow_run_id}</Descriptions.Item>
            <Descriptions.Item label='trace_id'>{focusRun.trace_id}</Descriptions.Item>
            <Descriptions.Item label='status'>{focusRun.status || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>
      ) : null}
    </Space>
  );
}


