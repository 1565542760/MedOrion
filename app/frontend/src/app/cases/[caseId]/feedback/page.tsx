'use client';

import Link from 'next/link';
import { use, useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Switch, Table, Tag, Typography } from 'antd';
import { createFeedback, getRecommendations, getTraceEvents, listFeedback, readCurrentUser, type DoctorFeedbackItem } from '@/lib/api';

type FeedbackRow = DoctorFeedbackItem & { key: string; source: 'backend' | 'local' };

type FeedbackFormValues = {
  trace_id?: string;
  recommendation_id?: string;
  feedback_type?: string;
  doctor_decision?: string;
  rating?: number | null;
  feedback_text?: string;
  learning_eligible?: boolean;
};

const LOCAL_CACHE_KEY = 'medorion_feedback_local_cache';
const T = (value: string) => value;

function readLocalFeedback(caseId: string): DoctorFeedbackItem[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(LOCAL_CACHE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as Record<string, DoctorFeedbackItem[]>;
    return Array.isArray(parsed[caseId]) ? parsed[caseId] : [];
  } catch {
    return [];
  }
}

function saveLocalFeedback(caseId: string, items: DoctorFeedbackItem[]) {
  if (typeof window === 'undefined') return;
  const raw = window.localStorage.getItem(LOCAL_CACHE_KEY);
  const parsed = raw ? JSON.parse(raw) as Record<string, DoctorFeedbackItem[]> : {};
  parsed[caseId] = items;
  window.localStorage.setItem(LOCAL_CACHE_KEY, JSON.stringify(parsed));
}

function normalizeError(error: unknown) {
  const response = (error as { response?: { status?: number; data?: { detail?: { code?: string } | string; code?: string } } })?.response;
  const code = response?.data?.detail && typeof response.data.detail === 'object'
    ? response.data.detail.code
    : response?.data?.code;
  if (code === 'trace_mismatch') return T('提交失败：trace_id 与当前病例不匹配');
  if (code === 'case_not_found') return T('提交失败：病例不存在');
  if (code === 'recommendation_not_found') return T('提交失败：推荐结果不存在');
  if (response?.status === 404) return T('提交失败：后端反馈写入接口当前不可用（404）');
  if (response?.status === 422) return T('提交失败：反馈字段校验未通过');
  return T('提交失败：请稍后重试');
}

function makeKey(row: DoctorFeedbackItem) {
  return row.feedback_id || [row.case_id, row.trace_id, row.recommendation_id, row.feedback_type, row.created_at].filter(Boolean).join('|');
}

function makeLocalFeedback(values: FeedbackFormValues, caseId: string) {
  const currentUser = readCurrentUser();
  const now = new Date().toISOString();
  return {
    feedback_id: 'local-' + Date.now().toString() + '-' + Math.random().toString(36).slice(2),
    case_id: caseId,
    trace_id: values.trace_id || '',
    recommendation_id: values.recommendation_id || '',
    feedback_type: values.feedback_type || 'comment',
    feedback_text: values.feedback_text || null,
    doctor_decision: values.doctor_decision || null,
    rating: values.rating ?? null,
    doctor_id: currentUser?.user_id || currentUser?.username || 'dev_doctor',
    learning_eligible: values.learning_eligible ?? true,
    created_at: now,
    updated_at: now,
  } as DoctorFeedbackItem;
}

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const searchParams = useSearchParams();
  const [form] = Form.useForm<FeedbackFormValues>();
  const traceParam = searchParams.get('trace_id') || '';
  const watchedTrace = Form.useWatch('trace_id', form) || '';
  const recommendationParam = searchParams.get('recommendation_id') || '';
  const [rows, setRows] = useState<FeedbackRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [prefilling, setPrefilling] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'info' | 'warning' | 'error'>('info');

  const initialValues = useMemo<FeedbackFormValues>(() => ({
    trace_id: traceParam,
    recommendation_id: recommendationParam,
    feedback_type: 'comment',
    doctor_decision: 'reviewed',
    rating: 4,
    feedback_text: '',
    learning_eligible: true,
  }), [recommendationParam, traceParam]);

  const refreshFeedback = useCallback(async () => {
    setLoading(true);
    try {
      const backend = await listFeedback(caseId);
      const local = readLocalFeedback(caseId);
      const merged = [...backend.items, ...local].reduce<DoctorFeedbackItem[]>((acc, item) => {
        if (!acc.some((row) => row.feedback_id === item.feedback_id)) acc.push(item);
        return acc;
      }, []);
      setRows(merged.map((row) => ({ ...row, key: makeKey(row), source: row.feedback_id.startsWith('local-') ? 'local' : 'backend' })));
    } catch (error) {
      setMessageType('error');
      setMessage(T('加载历史反馈失败：') + (error instanceof Error ? error.message : T('请稍后重试')));
      setRows(readLocalFeedback(caseId).map((row) => ({ ...row, key: makeKey(row), source: 'local' })));
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    form.setFieldsValue(initialValues);
  }, [form, initialValues]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshFeedback();
  }, [refreshFeedback]);

  async function handleFillLatestRecommendation() {
    const currentTrace = watchedTrace || traceParam || '';
    setPrefilling(true);
    setMessage('');
    try {
      if (currentTrace) {
        const events = await getTraceEvents(currentTrace);
        const latestRecommendation = events.find((event) => {
          const payload = event?.payload as { recommendation_id?: string } | undefined;
          return event?.event_type === 'recommendation_generated' && Boolean(payload?.recommendation_id || event?.source_record_id);
        });
        const recommendationId = (latestRecommendation?.payload as { recommendation_id?: string } | undefined)?.recommendation_id || latestRecommendation?.source_record_id;
        if (recommendationId) {
          form.setFieldsValue({ recommendation_id: recommendationId });
          setMessageType('info');
          setMessage(T('\u5df2\u586b\u5165\u6700\u8fd1\u4e00\u6b21\u63a8\u8350\u7ed3\u679c ID'));
          return;
        }
      }

      const items = await getRecommendations(caseId, currentTrace || undefined);
      const first = Array.isArray(items)
        ? (items[0] as { recommendation_id?: string; item_id?: string; id?: string; source_record_id?: string } | undefined)
        : undefined;
      const recommendationId = first?.recommendation_id || first?.item_id || first?.id || first?.source_record_id;
      if (!recommendationId) {
        setMessageType('warning');
        setMessage(T('\u672a\u627e\u5230\u53ef\u7528\u63a8\u8350\u7ed3\u679c\uff0c\u8bf7\u624b\u52a8\u8f93\u5165 recommendation_id'));
        return;
      }
      form.setFieldsValue({ recommendation_id: recommendationId });
      setMessageType('info');
      setMessage(T('\u5df2\u586b\u5165\u6700\u8fd1\u4e00\u6b21\u63a8\u8350\u7ed3\u679c ID'));
    } catch (error) {
      setMessageType('warning');
      setMessage(T('\u586b\u5165\u63a8\u8350\u7ed3\u679c\u5931\u8d25\uff1a') + (error instanceof Error ? error.message : T('\u8bf7\u624b\u52a8\u8f93\u5165 recommendation_id')));
    } finally {
      setPrefilling(false);
    }
  }

  async function handleSubmit(values: FeedbackFormValues) {
    setSubmitting(true);
    setMessage('');
    try {
      const payload = {
        case_id: caseId,
        trace_id: values.trace_id || undefined,
        recommendation_id: values.recommendation_id || '',
        feedback_type: values.feedback_type || 'comment',
        feedback_text: values.feedback_text || undefined,
        doctor_decision: values.doctor_decision || undefined,
        rating: typeof values.rating === 'number' ? values.rating : undefined,
        learning_eligible: values.learning_eligible ?? true,
      };
      const created = await createFeedback(payload);
      setMessageType('info');
      setMessage(T('医生反馈已提交并刷新历史列表'));
      if (created.feedback_id.startsWith('local-')) {
        const local = readLocalFeedback(caseId);
        saveLocalFeedback(caseId, [created, ...local].reduce<DoctorFeedbackItem[]>((acc, item) => {
          if (!acc.some((row) => row.feedback_id === item.feedback_id)) acc.push(item);
          return acc;
        }, []));
      }
      form.resetFields(['feedback_text']);
      await refreshFeedback();
    } catch (error) {
      const msg = normalizeError(error);
      if (msg.includes('404')) {
        const draft = makeLocalFeedback(values, caseId);
        const local = readLocalFeedback(caseId);
        saveLocalFeedback(caseId, [draft, ...local].reduce<DoctorFeedbackItem[]>((acc, item) => {
          if (!acc.some((row) => row.feedback_id === item.feedback_id)) acc.push(item);
          return acc;
        }, []));
        setMessageType('warning');
        setMessage(T('后端反馈写入接口当前不可用，已先保存为本地开发草稿并刷新列表'));
        setRows((prev) => {
          const next = [draft, ...prev].reduce<FeedbackRow[]>((acc, item) => {
            if (!acc.some((row) => row.feedback_id === item.feedback_id)) {
              acc.push({ ...item, key: makeKey(item), source: item.feedback_id.startsWith('local-') ? 'local' : 'backend' });
            }
            return acc;
          }, []);
          return next;
        });
      } else {
        setMessageType('error');
        setMessage(msg);
      }
    } finally {
      setSubmitting(false);
    }
  }

  const traceLink = watchedTrace ? '/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(watchedTrace) : '';

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>{T('医生反馈')}</Typography.Title>
      <Typography.Text type='secondary'>{T('病例：')}{caseId}</Typography.Text>

      <Alert
        type='info'
        showIcon
        message={T('医生反馈不会直接修改模型')}
        description={T('learning_eligible 只是后续受控离线学习入口，不代表自动训练。')}
      />

      {message ? <Alert type={messageType} showIcon message={message} /> : null}

      <Card title={T('提交医生反馈')}>
        <Form layout='vertical' form={form} initialValues={initialValues} onFinish={handleSubmit}>
          <Space direction='vertical' size={0} style={{ width: '100%' }}>
            <Form.Item label='trace_id' name='trace_id' rules={[{ required: true, message: T('请输入 trace_id') }]}>
              <Input placeholder={T('例如：trace_stub_xxx')} />
            </Form.Item>
            <Form.Item label='recommendation_id' name='recommendation_id' rules={[{ required: true, message: T('请输入 recommendation_id') }]}>
              <Input placeholder={T('例如：268c6307-...')} />
            </Form.Item>
            <Space wrap style={{ marginBottom: 16 }}>
              <Button onClick={() => void handleFillLatestRecommendation()} loading={prefilling}>{T('填入最近推荐 ID')}</Button>
              <Tag color='blue'>{T('开发态可手动输入 recommendation_id')}</Tag>
            </Space>
            <Space size={16} style={{ width: '100%' }} wrap align='start'>
              <Form.Item label='feedback_type' name='feedback_type' rules={[{ required: true, message: T('请选择反馈类型') }]} style={{ minWidth: 220 }}>
                <Select
                  options={[
                    { label: 'comment', value: 'comment' },
                    { label: 'agreement', value: 'agreement' },
                    { label: 'disagreement', value: 'disagreement' },
                    { label: 'safety', value: 'safety' },
                    { label: 'other', value: 'other' },
                  ]}
                />
              </Form.Item>
              <Form.Item label='doctor_decision' name='doctor_decision' style={{ minWidth: 220 }}>
                <Input placeholder={T('如： reviewed / accepted / rejected')} />
              </Form.Item>
              <Form.Item label='rating' name='rating' style={{ minWidth: 160 }}>
                <InputNumber min={1} max={5} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item label='learning_eligible' name='learning_eligible' valuePropName='checked' style={{ minWidth: 220 }}>
                <Switch checkedChildren={T('是')} unCheckedChildren={T('否')} />
              </Form.Item>
            </Space>
            <Form.Item label='feedback_text' name='feedback_text'>
              <Input.TextArea rows={4} placeholder={T('输入医生反馈内容')} />
            </Form.Item>
            <Space wrap>
              <Button type='primary' htmlType='submit' loading={submitting}>{T('提交医生反馈')}</Button>
              {traceLink ? <Link href={traceLink}>{T('查看溯源')}</Link> : null}
            </Space>
          </Space>
        </Form>
      </Card>

      <Card title={T('历史反馈')}>
        <Table
          rowKey='feedback_id'
          loading={loading}
          dataSource={rows}
          pagination={false}
          scroll={{ x: 1800 }}
          columns={[
            { title: 'feedback_id', dataIndex: 'feedback_id', width: 180, render: (v: string) => v || '-' },
            { title: 'trace_id', dataIndex: 'trace_id', width: 180, render: (v: string) => <Space wrap><span>{v || '-'}</span>{v ? <Link href={'/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(v)}>{T('查看溯源')}</Link> : null}</Space> },
            { title: 'recommendation_id', dataIndex: 'recommendation_id', width: 220, render: (v: string) => v || '-' },
            { title: 'feedback_type', dataIndex: 'feedback_type', width: 140, render: (v: string) => <Tag>{v || '-'}</Tag> },
            { title: 'feedback_text', dataIndex: 'feedback_text', width: 280, render: (v: string) => v || '-' },
            { title: 'doctor_decision', dataIndex: 'doctor_decision', width: 180, render: (v: string) => v || '-' },
            { title: 'rating', dataIndex: 'rating', width: 100, render: (v: number) => (typeof v === 'number' ? v : '-') },
            { title: 'learning_eligible', dataIndex: 'learning_eligible', width: 180, render: (v: boolean) => <Tag color={v ? 'green' : 'gold'}>{v ? T('是－受控离线学习候选') : T('否－仅归档')}</Tag> },
            { title: T('\u6765\u6e90'), dataIndex: 'source', width: 120, render: (v: string) => <Tag color={v === 'local' ? 'gold' : 'blue'}>{v === 'local' ? T('\u672c\u5730\u8349\u7a3f') : T('\u540e\u7aef\u771f\u5b9e\u8bb0\u5f55')}</Tag> },
            { title: 'doctor_id', dataIndex: 'doctor_id', width: 180, render: (v: string) => v || '-' },
            { title: 'created_at', dataIndex: 'created_at', width: 220, render: (v: string) => v || '-' },
          ]}
        />
      </Card>
    </Space>
  );
}
