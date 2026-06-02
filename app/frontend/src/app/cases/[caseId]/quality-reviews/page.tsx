'use client';

import Link from 'next/link';
import { use, useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Alert, Button, Card, Form, Input, Select, Space, Table, Tag, Typography } from 'antd';
import { createQualityReview, listQualityReviewsByCase, type QualityReviewItem } from '@/lib/api';

type ReviewRow = QualityReviewItem & { key: string; opened_by_display: string };

type ReviewFormValues = {
  trace_id?: string;
  target_type?: string;
  target_id?: string;
  attribution?: string;
  severity?: string;
  summary?: string;
  related_feedback_id?: string;
};

const T = (value: string) => value;

function normalizeError(error: unknown) {
  const response = (error as { response?: { status?: number; data?: { detail?: { code?: string } | string; code?: string } } })?.response;
  const code = response?.data?.detail && typeof response.data.detail === 'object'
    ? response.data.detail.code
    : response?.data?.code;
  if (code === 'case_not_found') return T('提交失败：病例不存在');
  if (code === 'trace_not_found') return T('提交失败：trace_id 不存在');
  if (code === 'feedback_not_found') return T('提交失败：related_feedback_id 不存在');
  if (code === 'trace_mismatch') return T('提交失败：trace_id 与当前 case 不匹配');
  if (code === 'invalid_target_type') return T('提交失败：target_type 无效');
  if (code === 'invalid_attribution') return T('提交失败：attribution 无效');
  if (response?.status === 404) return T('提交失败：后端质控审查接口不可用（404）');
  if (response?.status === 422) return T('提交失败：质控字段校验未通过');
  return T('提交失败：请稍后重试');
}

function makeKey(row: QualityReviewItem) {
  return row.review_id || [row.case_id, row.trace_id, row.target_type, row.target_id, row.created_at].filter(Boolean).join('|');
}

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const searchParams = useSearchParams();
  const [form] = Form.useForm<ReviewFormValues>();
  const traceParam = searchParams.get('trace_id') || '';
  const targetTypeParam = searchParams.get('target_type') || 'recommendation';
  const targetIdParam = searchParams.get('target_id') || '';
  const relatedFeedbackParam = searchParams.get('related_feedback_id') || '';
  const severityParam = searchParams.get('severity') || 'medium';
  const summaryParam = searchParams.get('summary') || '';
  const attributionParam = searchParams.get('attribution') || 'human_feedback';
  const watchedTrace = Form.useWatch('trace_id', form) || '';
  const [rows, setRows] = useState<ReviewRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'info' | 'warning' | 'error'>('info');

  const initialValues = useMemo<ReviewFormValues>(() => ({
    trace_id: traceParam,
    target_type: targetTypeParam,
    target_id: targetIdParam,
    attribution: attributionParam,
    severity: severityParam,
    summary: summaryParam,
    related_feedback_id: relatedFeedbackParam,
  }), [attributionParam, relatedFeedbackParam, severityParam, summaryParam, targetIdParam, targetTypeParam, traceParam]);

  const refreshReviews = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listQualityReviewsByCase(caseId);
      const items = data.items || [];
      setRows(items.map((item) => ({
        ...item,
        key: makeKey(item),
        opened_by_display: item.opened_by || item.actor_id || '-',
      })));
    } catch (error) {
      setMessageType('error');
      setMessage(T('加载质控审查列表失败：') + (error instanceof Error ? error.message : T('请稍后重试')));
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    form.setFieldsValue(initialValues);
  }, [form, initialValues]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshReviews();
  }, [refreshReviews]);

  async function handleSubmit(values: ReviewFormValues) {
    setSubmitting(true);
    setMessage('');
    try {
      const payload = {
        case_id: caseId,
        trace_id: values.trace_id || undefined,
        target_type: values.target_type || 'recommendation',
        target_id: values.target_id || '',
        attribution: values.attribution || 'human_feedback',
        severity: values.severity || 'medium',
        summary: values.summary || '',
        related_feedback_id: values.related_feedback_id || undefined,
      };
      await createQualityReview(payload);
      setMessageType('info');
      setMessage(T('质控审查已提交并刷新列表'));
      form.resetFields();
      form.setFieldsValue({
        trace_id: values.trace_id,
        target_type: values.target_type || 'recommendation',
        target_id: values.target_id,
        attribution: values.attribution || 'human_feedback',
        severity: values.severity || 'medium',
      });
      await refreshReviews();
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setSubmitting(false);
    }
  }

  const traceLink = watchedTrace ? '/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(watchedTrace) : '';

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>{T('质控审查')}</Typography.Title>
      <Typography.Text type='secondary'>{T('病例：')}{caseId}</Typography.Text>

      <Alert
        type='info'
        showIcon
        message={T('质控审查不会自动修改 recommendation，也不会触发模型训练。')}
        description={T('可从病例反馈页带入 case_id、trace_id 和 related_feedback_id，再补充 target_type 、target_id 与 summary。')}
      />

      {message ? <Alert type={messageType} showIcon message={message} /> : null}

      <Card title={T('创建质控审查')}>
        <Form layout='vertical' form={form} initialValues={initialValues} onFinish={handleSubmit}>
          <Space direction='vertical' size={0} style={{ width: '100%' }}>
            <Form.Item label='trace_id' name='trace_id' rules={[{ required: true, message: T('请输入 trace_id') }]}>
              <Input placeholder={T('例如：trace_stub_xxx')} />
            </Form.Item>
            <Form.Item label='target_type' name='target_type' rules={[{ required: true, message: T('请输入 target_type') }]}>
              <Input placeholder={T('例如：recommendation')} />
            </Form.Item>
            <Form.Item label='target_id' name='target_id' rules={[{ required: true, message: T('请输入 target_id') }]}>
              <Input placeholder={T('例如：cf03dd23-...')} />
            </Form.Item>
            <Form.Item label='attribution' name='attribution' rules={[{ required: true, message: T('请输入 attribution') }]}>
              <Input placeholder={T('例如：human_feedback')} />
            </Form.Item>
            <Space size={16} style={{ width: '100%' }} wrap align='start'>
              <Form.Item label='severity' name='severity' style={{ minWidth: 200 }}>
                <Select
                  options={[
                    { label: 'low', value: 'low' },
                    { label: 'medium', value: 'medium' },
                    { label: 'high', value: 'high' },
                    { label: 'critical', value: 'critical' },
                  ]}
                />
              </Form.Item>
              <Form.Item label='related_feedback_id' name='related_feedback_id' style={{ minWidth: 360 }}>
                <Input placeholder={T('\u53ef\u9009\uff0c\u53d7\u53cd\u9988\u9875\u5e26\u5165')} />
              </Form.Item>
            </Space>
            <Form.Item label='summary' name='summary' rules={[{ required: true, message: T('请输入 summary') }]}>
              <Input.TextArea rows={4} placeholder={T('输入质控审查摘要')} />
            </Form.Item>
            <Space wrap>
              <Button type='primary' htmlType='submit' loading={submitting}>{T('创建质控审查')}</Button>
              {traceLink ? <Link href={traceLink}>{T('查看溯源')}</Link> : null}
            </Space>
          </Space>
        </Form>
      </Card>

      <Card title={T('质控审查列表')}>
        <Table
          rowKey='review_id'
          loading={loading}
          dataSource={rows}
          pagination={false}
          scroll={{ x: 1800 }}
          columns={[
            { title: 'review_id', dataIndex: 'review_id', width: 180, render: (v: string) => v || '-' },
            { title: 'case_id', dataIndex: 'case_id', width: 200, render: (v: string) => v || '-' },
            { title: 'trace_id', dataIndex: 'trace_id', width: 180, render: (v: string) => <Space wrap><span>{v || '-'}</span>{v ? <Link href={'/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(v)}>{T('查看溯源')}</Link> : null}</Space> },
            { title: 'target_type', dataIndex: 'target_type', width: 160, render: (v: string) => <Tag>{v || '-'}</Tag> },
            { title: 'target_id', dataIndex: 'target_id', width: 240, render: (v: string) => v || '-' },
            { title: 'status', dataIndex: 'status', width: 120, render: (v: string) => <Tag color={v === 'open' ? 'blue' : 'green'}>{v || '-'}</Tag> },
            { title: 'attribution', dataIndex: 'attribution', width: 180, render: (v: string) => v || '-' },
            { title: 'severity', dataIndex: 'severity', width: 120, render: (v: string) => <Tag color={v === 'critical' ? 'red' : v === 'high' ? 'volcano' : 'blue'}>{v || '-'}</Tag> },
            { title: 'summary', dataIndex: 'summary', width: 280, render: (v: string) => v || '-' },
            { title: 'related_feedback_id', dataIndex: 'related_feedback_id', width: 220, render: (v: string) => v || '-' },
            { title: 'opened_by', dataIndex: 'opened_by_display', width: 180, render: (v: string) => v || '-' },
            { title: 'created_at', dataIndex: 'created_at', width: 220, render: (v: string) => v || '-' },
          ]}
        />
      </Card>
    </Space>
  );
}
