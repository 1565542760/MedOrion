'use client';

import Link from 'next/link';
import { use, useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Input, Space, Table, Tag, Typography } from 'antd';
import {
  applyDefaultMissingValueQuery,
  answerMissingValueQuery,
  createMissingValueQuery,
  listMissingValueQueries,
  MissingValueQuery,
} from '@/lib/api';

type QueryRow = MissingValueQuery & { key: string };

const DEMO_DEFAULT_STRATEGY_CODE = 'demo_default';
const DEMO_DEFAULT_REASON = '演示默认策略';
const DEMO_DEFAULT_VALUE_JSON = { value: 'demo-default' };

function makeKey(row: MissingValueQuery) {
  return (
    row.query_id ||
    row.field_name ||
    row.trace_id ||
    [row.case_id, row.patient_id, row.field_name, row.question_text].filter(Boolean).join('|') ||
    JSON.stringify({
      case_id: row.case_id || '',
      patient_id: row.patient_id || '',
      field_name: row.field_name || '',
      question_text: row.question_text || '',
    })
  );
}

function statusTag(row: MissingValueQuery) {
  if (row.status === 'default_applied' || row.value_source === 'default_applied') {
    return <Tag color='blue'>默认策略已应用</Tag>;
  }
  if (row.status === 'answered' || row.value_source === 'doctor_provided') {
    return <Tag color='green'>医生已回答</Tag>;
  }
  return <Tag color='gold'>待处理</Tag>;
}

function valueSourceTag(row: MissingValueQuery) {
  if (row.value_source === 'doctor_provided') return <Tag color='green'>doctor_provided</Tag>;
  if (row.value_source === 'default_applied') return <Tag color='blue'>default_applied</Tag>;
  if (row.value_source) return <Tag>{row.value_source}</Tag>;
  return '-';
}

function traceLink(caseId: string, traceId?: string | null) {
  if (!traceId) return '-';
  return <Link href={'/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(traceId)}>查看溯源</Link>;
}

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [rows, setRows] = useState<QueryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState<{ queryId: string; kind: 'answer' | 'default' | 'create' } | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  const loadQueries = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listMissingValueQueries(caseId);
      const normalized = (data.items || []).map((row) => ({ ...row, key: makeKey(row) }));
      setRows(normalized);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载失败';
      setError('加载缺失值咨询失败：' + msg);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadQueries();
  }, [loadQueries]);

  const pendingCount = useMemo(() => rows.filter((row) => row.status === 'pending' && row.value_source !== 'default_applied').length, [rows]);

  async function handleCreateDemoQuery() {
    setCreating(true);
    setError('');
    try {
      await createMissingValueQuery(caseId, {
        field_name: 'wbc',
        field_label: '白细胞',
        modality: 'lab',
        reason: 'demo',
        question_text: '请补充白细胞值',
        trace_id: 'trace-demo',
        value_source: 'unknown',
        default_strategy_code: DEMO_DEFAULT_STRATEGY_CODE,
        default_reason: DEMO_DEFAULT_REASON,
      }, 'trace-demo');
      await loadQueries();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '调用失败';
      setError('创建缺失值咨询失败：' + msg);
    } finally {
      setCreating(false);
    }
  }

  async function handleAnswer(row: MissingValueQuery) {
    const answerText = (drafts[row.query_id] || '').trim();
    if (!answerText) {
      setError('请先输入医生回答');
      return;
    }
    setBusy({ queryId: row.query_id, kind: 'answer' });
    setError('');
    try {
      await answerMissingValueQuery(caseId, row.query_id, {
        doctor_answer_text: answerText,
        doctor_answer_json: { value: answerText },
      }, row.trace_id || 'trace-demo');
      setDrafts((prev) => ({ ...prev, [row.query_id]: '' }));
      await loadQueries();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '调用失败';
      setError('提交医生回答失败：' + msg);
    } finally {
      setBusy(null);
    }
  }

  async function handleApplyDefault(row: MissingValueQuery) {
    setBusy({ queryId: row.query_id, kind: 'default' });
    setError('');
    try {
      await applyDefaultMissingValueQuery(caseId, row.query_id, {
        default_strategy_code: DEMO_DEFAULT_STRATEGY_CODE,
        default_reason: DEMO_DEFAULT_REASON,
        default_value_json: DEMO_DEFAULT_VALUE_JSON,
      }, row.trace_id || 'trace-demo');
      await loadQueries();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '调用失败';
      setError('应用默认策略失败：' + msg);
    } finally {
      setBusy(null);
    }
  }

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>缺失值咨询</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}</Typography.Text>

      <Alert
        type='info'
        showIcon
        message='当前为 stub/demo 联调，不用于医学诊断'
        description='页面支持创建缺失值咨询、医生回答、应用默认策略，并保留 trace_id 入口。'
      />

      {error ? <Alert type='error' showIcon message={error} /> : null}

      <Card>
        <Space wrap>
          <Button type='primary' loading={creating} onClick={handleCreateDemoQuery}>创建 demo 缺失值咨询</Button>
          <Tag color='gold'>待处理 {pendingCount}</Tag>
          <Tag color='blue'>当前总数 {rows.length}</Tag>
        </Space>
      </Card>

      <Card>
        <Table
          rowKey='query_id'
          loading={loading}
          dataSource={rows}
          pagination={false}
          scroll={{ x: 1800 }}
          columns={[
            { title: 'field_name', dataIndex: 'field_name', width: 120 },
            { title: 'field_label', dataIndex: 'field_label', width: 140, render: (v: string) => v || '-' },
            { title: 'modality', dataIndex: 'modality', width: 100, render: (v: string) => v || '-' },
            { title: 'reason', dataIndex: 'reason', width: 120, render: (v: string) => v || '-' },
            { title: 'question_text', dataIndex: 'question_text', width: 220, render: (v: string) => v || '-' },
            { title: 'status', dataIndex: 'status', width: 140, render: (_: string, row: MissingValueQuery) => statusTag(row) },
            { title: 'trace_id', dataIndex: 'trace_id', width: 180, render: (_: string, row: MissingValueQuery) => <Space wrap><span>{row.trace_id || '-'}</span>{traceLink(caseId, row.trace_id)}</Space> },
            { title: 'value_source', dataIndex: 'value_source', width: 160, render: (_: string, row: MissingValueQuery) => valueSourceTag(row) },
            { title: 'default_strategy_code', dataIndex: 'default_strategy_code', width: 180, render: (v: string) => v || '-' },
            { title: 'default_reason', dataIndex: 'default_reason', width: 180, render: (v: string) => v || '-' },
            {
              title: '操作',
              width: 360,
              render: (_: unknown, row: MissingValueQuery) => {
                const answerLoading = busy?.queryId === row.query_id && busy.kind === 'answer';
                const defaultLoading = busy?.queryId === row.query_id && busy.kind === 'default';
                const canAct = row.status === 'pending' || row.value_source === 'unknown' || !row.status;
                return canAct ? (
                  <Space direction='vertical' size={8} style={{ width: '100%' }}>
                    <Input
                      size='small'
                      placeholder='输入医生回答'
                      value={drafts[row.query_id] || ''}
                      onChange={(e) => setDrafts((prev) => ({ ...prev, [row.query_id]: e.target.value }))}
                    />
                    <Space wrap>
                      <Button size='small' type='primary' loading={answerLoading} onClick={() => void handleAnswer(row)}>医生回答</Button>
                      <Button size='small' loading={defaultLoading} onClick={() => void handleApplyDefault(row)}>应用默认策略</Button>
                    </Space>
                  </Space>
                ) : (
                  <Tag>已完成</Tag>
                );
              }
            }
          ]}
        />
      </Card>
    </Space>
  );
}
