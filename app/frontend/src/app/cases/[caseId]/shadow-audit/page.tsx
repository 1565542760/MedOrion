'use client';

import Link from 'next/link';
import axios from 'axios';
import { use, useEffect, useMemo, useState } from 'react';
import { Alert, Card, Descriptions, Empty, Space, Spin, Table, Tag, Typography } from 'antd';
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

function translateError(error: unknown) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const data = error.response?.data as { detail?: { code?: string; message?: string } | string; code?: string; message?: string } | undefined;
    const code = typeof data?.detail === 'string' ? data.detail : (data?.detail && typeof data.detail === 'object' ? data.detail.code : data?.code || data?.message || '');
    if (status === 404 || code === 'shadow_run_not_found') return 'shadow 审计记录未找到';
    if (status === 422) return 'shadow 审计参数校验失败';
    if (code) return 'shadow 审计请求失败：' + code;
  }
  if (error instanceof Error) return error.message;
  return 'shadow 审计请求失败';
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
        const listResponse = traceId
          ? await listShadowRunsByTrace(traceId)
          : await listShadowRunsByCase(caseId);
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

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>Shadow 审计查看</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}{traceId ? ' · trace_id：' + traceId : ''}</Typography.Text>

      <Alert
        type='info'
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
                          <Empty description='暂无 outputs' />
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

