'use client';

import Link from 'next/link';
import { use, useMemo, useState } from 'react';
import { Alert, Button, Card, Descriptions, Space, Statistic, Typography } from 'antd';
import { createInferenceTask, InferenceTaskPayload, InferenceTaskResponse } from '@/lib/api';

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<InferenceTaskResponse | null>(null);

  const payloadBase = useMemo(() => ({
    patient_id: 'patient-001',
    disease_agent: 'capcop_agent',
    requested_task: 'risk_assessment',
    model_version_policy: { mode: 'latest_approved', pinned_version: 'capcop_stub_v1' },
    inputs: { ct: 'stub://ct/1', labs: { wbc: 11.2 } },
    missing_value_context: { pending_queries: [] },
  }), []);

  async function handleRunStubInference() {
    setRunning(true);
    setError('');
    try {
      const payload: InferenceTaskPayload = {
        ...payloadBase,
        idempotency_key: 'idem-' + caseId + '-' + Date.now().toString(),
      };
      const data = await createInferenceTask(caseId, payload);
      setResult(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '调用失败';
      setError('模拟推理调用失败：' + msg);
    } finally {
      setRunning(false);
    }
  }

  const confidenceText = typeof result?.confidence === 'object'
    ? JSON.stringify(result?.confidence ?? {})
    : (result?.confidence ?? '-');

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>小模型分析结果</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}</Typography.Text>

      <Alert type='warning' showIcon message='当前为 stub/demo 链路验证' description='未加载真实模型，不用于医学诊断。' />

      <Card title='风险占位信息'>
        <Space size={24}>
          <Statistic title='肺炎风险(占位)' value={0.73} precision={2} />
          <Statistic title='败血风险(占位)' value={0.21} precision={2} />
        </Space>
      </Card>

      <Card title='模型输入预览'>
        <Space direction='vertical' size={8}>
          <Typography.Text type='secondary'>先查看模型输入 schema，再回来做模型选择和规则校验。</Typography.Text>
          <Link href={'/cases/' + caseId + '/model-input'}>查看模型输入预览</Link>
        </Space>
      </Card>

      <Card title='Shadow 审计入口'>
        <Space direction='vertical' size={8}>
          <Typography.Text type='secondary'>Shadow audit 是旁路审计，不影响正式 recommendation，不是诊断结论，也不是医生替代。</Typography.Text>
          <Link href={'/cases/' + caseId + '/shadow-audit'}>查看 Shadow 审计</Link>
        </Space>
      </Card>

      <Card title='最小推理调用链验证'>
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Button type='primary' loading={running} onClick={handleRunStubInference}>运行模拟推理</Button>
          {error ? <Alert type='error' showIcon message={error} /> : null}
          {result ? (
            <Descriptions bordered size='small' column={1} title='推理返回关键字段'>
              <Descriptions.Item label='trace_id'>{result.trace_id || '-'}</Descriptions.Item>
              <Descriptions.Item label='task_id'>{result.task_id || '-'}</Descriptions.Item>
              <Descriptions.Item label='model_invocation_id'>{result.model_invocation_id || '-'}</Descriptions.Item>
              <Descriptions.Item label='model_version_id'>{result.model_version_id || '-'}</Descriptions.Item>
              <Descriptions.Item label='confidence'>{confidenceText}</Descriptions.Item>
              <Descriptions.Item label='uncertainty'>{JSON.stringify(result.uncertainty ?? {})}</Descriptions.Item>
              <Descriptions.Item label='limitations'>{JSON.stringify(result.limitations ?? [])}</Descriptions.Item>
              <Descriptions.Item label='recommendation.evidence_refs'>{JSON.stringify(result.recommendation?.evidence_refs ?? [])}</Descriptions.Item>
            </Descriptions>
          ) : null}
        </Space>
      </Card>
    </Space>
  );
}
