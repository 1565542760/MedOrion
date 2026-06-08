'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { Alert, Button, Card, Form, Input, Select, Space, Table, Tag, Typography } from 'antd';
import {
  createCase,
  createPatient,
  getShadowRunOutputs,
  listCases,
  listPatients,
  listShadowRunsByCase,
  type CaseItem,
  type PatientItem,
  type ShadowInferenceRunOutputItem,
} from '@/lib/api';

type CaseRow = CaseItem & {
  key?: string;
  patient_display_name?: string | null;
};

type NewCaseFormValues = {
  external_patient_id?: string;
  display_name?: string;
  sex?: string;
  case_no?: string;
  disease_task?: string;
  chief_complaint?: string;
};

type ShadowSummary = {
  shadow_run_id?: string | null;
  trace_id?: string | null;
  status?: string | null;
  candidate_label?: string | null;
  calibrated?: boolean | null;
  shadow_only?: boolean | null;
  not_for_diagnosis?: boolean | null;
  not_formal_recommendation?: boolean | null;
  error?: string | null;
};

const CASE_TABLE_SCROLL_WIDTH = 2220;

function makeCaseKey(row: CaseRow) {
  return (
    row.case_id ||
    row.case_no ||
    (row.patient_id && row.trace_id ? row.patient_id + '|' + row.trace_id : '') ||
    [row.patient_id, row.trace_id, row.disease_task, row.status].filter(Boolean).join('|') ||
    JSON.stringify({
      patient_id: row.patient_id || '',
      trace_id: row.trace_id || '',
      disease_task: row.disease_task || '',
      status: row.status || '',
      case_no: row.case_no || '',
    })
  );
}

function normalizeCaseError(error: unknown) {
  const response = (error as { response?: { status?: number; data?: { detail?: { code?: string } | string; code?: string } } })?.response;
  const detail = response?.data?.detail;
  const code = detail && typeof detail === 'object' ? detail.code : response?.data?.code;
  if (code === 'patient_not_found') return '创建失败：患者不存在';
  if (code === 'invalid_patient_id') return '创建失败：patient_id 不是有效 UUID';
  if (code === 'invalid_case_status') return '创建失败：病例状态不支持';
  if (code === 'case_conflict') return '创建失败：病例编号冲突或违反唯一约束';
  if (code === 'patient_conflict') return '创建失败：患者标识冲突或违反唯一约束';
  if (response?.status === 401) return '创建失败：请先登录';
  if (response?.status === 422) return '创建失败：表单参数校验未通过';
  return '创建失败：请稍后重试';
}

function pickPatientDisplayName(patient: PatientItem | undefined) {
  return patient?.display_name || patient?.external_patient_id || '-';
}

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

function getShadowStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'pending':
      return '待处理';
    case 'running':
      return '运行中';
    case 'completed':
      return '已完成';
    case 'failed':
      return '已失败';
    case 'shadow_failed':
      return '旁路失败';
    case 'shadow_completed':
      return '旁路已完成';
    case 'shadow_ready':
      return '旁路就绪';
    default:
      return value || '-';
  }
}

function getLatestShadowRunId(runs: { shadow_run_id: string; started_at?: string | null; created_at?: string | null }[]) {
  return [...runs].sort((a, b) => {
    const aTime = new Date(a.started_at || a.created_at || 0).getTime();
    const bTime = new Date(b.started_at || b.created_at || 0).getTime();
    return bTime - aTime;
  })[0]?.shadow_run_id || '';
}

function extractFlags(value: unknown) {
  if (Array.isArray(value)) return value.map((item) => String(item));
  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, item]) => {
      if (typeof item === 'boolean') return item ? [key] : [];
      if (typeof item === 'string') return [key + ': ' + item];
      if (typeof item === 'number') return [key + ': ' + String(item)];
      if (Array.isArray(item)) return item.map((entry) => key + ': ' + String(entry));
      return [] as string[];
    });
  }
  if (typeof value === 'string' && value.trim() !== '') return [value];
  return [] as string[];
}

function shadowLink(caseId: string, shadowRunId?: string | null) {
  return shadowRunId ? '/cases/' + caseId + '/shadow-audit?shadow_run_id=' + shadowRunId : '/cases/' + caseId + '/shadow-audit';
}

function ShadowCell({ caseId, summary }: { caseId: string; summary?: ShadowSummary }) {
  if (!summary) {
    return (
      <Space direction='vertical' size={4}>
        <Tag>暂无 shadow 输出</Tag>
        <Typography.Text type='secondary' style={{ fontSize: 12 }}>
          创建病例不会自动运行模型。请先看特征校验，再进入 Shadow 审计。
        </Typography.Text>
        <Space wrap size={8}>
          <Link href={'/cases/' + caseId + '/model-input'}>先看特征校验</Link>
          <Link href={'/cases/' + caseId + '/shadow-audit'}>查看 Shadow 审计</Link>
        </Space>
      </Space>
    );
  }
  if (summary.error) {
    return (
      <Space direction='vertical' size={4}>
        <Tag color='red'>shadow 审计读取失败</Tag>
        <Typography.Text type='secondary' style={{ fontSize: 12 }}>
          可以先进入特征校验页，或稍后重试。
        </Typography.Text>
        <Space wrap size={8}>
          <Link href={'/cases/' + caseId + '/model-input'}>先看特征校验</Link>
          <Link href={'/cases/' + caseId + '/shadow-audit'}>查看 Shadow 审计</Link>
        </Space>
      </Space>
    );
  }
  return (
    <Space direction='vertical' size={4}>
      <Space wrap size={6}>
        {summary.status ? <Tag>{getShadowStatusLabel(summary.status)}</Tag> : null}
        {summary.candidate_label ? <Tag color='gold'>旁路候选：{summary.candidate_label}</Tag> : null}
        {summary.calibrated === false ? <Tag color='orange'>未校准</Tag> : null}
        {summary.shadow_only ? <Tag>Shadow only</Tag> : null}
        {summary.not_for_diagnosis ? <Tag>Not for diagnosis / 非诊断</Tag> : null}
        {summary.not_formal_recommendation ? <Tag>Not a formal recommendation / 非正式推荐</Tag> : null}
      </Space>
      <Space wrap size={8}>
        <Link href={shadowLink(caseId, summary.shadow_run_id)}>查看审计</Link>
        <Link href={'/cases/' + caseId + '/model-input'}>先看特征校验</Link>
      </Space>
    </Space>
  );
}

export default function CasesPage() {
  const [form] = Form.useForm<NewCaseFormValues>();
  const [rows, setRows] = useState<CaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [shadowLoading, setShadowLoading] = useState(false);
  const [shadowSummaries, setShadowSummaries] = useState<Record<string, ShadowSummary>>({});
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'info' | 'warning' | 'error'>('info');
  const [createdCaseId, setCreatedCaseId] = useState('');
  const tableShellRef = useRef<HTMLDivElement | null>(null);
  const stickyScrollRef = useRef<HTMLDivElement | null>(null);
  const [stickyScrollWidth, setStickyScrollWidth] = useState(CASE_TABLE_SCROLL_WIDTH);

  async function loadCases(showLoading: boolean = true) {
    if (showLoading) setLoading(true);
    try {
      const [caseData, patientData] = await Promise.allSettled([listCases(), listPatients()]);
      const cases = caseData.status === 'fulfilled' ? caseData.value : [];
      const patients = patientData.status === 'fulfilled' ? patientData.value : [];
      const patientNameMap = new Map(patients.map((item) => [item.patient_id, pickPatientDisplayName(item)]));
      const normalized = Array.isArray(cases)
        ? (cases as CaseRow[]).map((row) => ({
            ...row,
            key: makeCaseKey(row),
            patient_display_name: patientNameMap.get(row.patient_id) || '-',
          }))
        : [];
      setRows(normalized);
      if (caseData.status === 'rejected') {
        setMessageType('error');
        setMessage('病例列表加载失败，请确认后端服务和登录状态。');
      }
    } catch {
      setRows([]);
      setMessageType('error');
      setMessage('病例列表加载失败，请确认后端服务和登录状态。');
    } finally {
      setLoading(false);
    }
  }

  async function loadShadowSummaries(caseRows: CaseRow[]) {
    if (caseRows.length === 0) {
      setShadowSummaries({});
      return;
    }
    setShadowLoading(true);
    try {
      const pairs = await Promise.all(
        caseRows.map(async (row) => {
          try {
            const runs = await listShadowRunsByCase(row.case_id);
            const latestRunId = getLatestShadowRunId(runs.items || []);
            const latestRun = (runs.items || []).find((item) => item.shadow_run_id === latestRunId) || null;
            if (!latestRun) {
              return [row.case_id, undefined] as const;
            }
            const outputs = await getShadowRunOutputs(latestRun.shadow_run_id).catch(() => ({ items: [] as ShadowInferenceRunOutputItem[], total: 0 }));
            const output = outputs.items?.[0] || null;
            const flags = extractFlags(output?.limitations_json);
            const calibrated = (output?.confidence_json as { calibrated?: boolean } | null | undefined)?.calibrated ?? null;
            return [row.case_id, {
              shadow_run_id: latestRun.shadow_run_id,
              trace_id: latestRun.trace_id,
              status: latestRun.status || null,
              candidate_label: output?.candidate_label || null,
              calibrated: calibrated === false || flags.includes('probability_uncalibrated') ? false : null,
              shadow_only: latestRun.runtime_stub ?? true,
              not_for_diagnosis: latestRun.not_for_diagnosis ?? true,
              not_formal_recommendation: true,
            }] as const;
          } catch {
            return [row.case_id, { error: '读取失败' }] as const;
          }
        })
      );
      setShadowSummaries(Object.fromEntries(pairs) as Record<string, ShadowSummary>);
    } finally {
      setShadowLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    void (async () => {
      await loadCases();
      if (!active) return;
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    void (async () => {
      await loadShadowSummaries(rows);
      if (!active) return;
    })();
    return () => {
      active = false;
    };
  }, [rows]);

  useEffect(() => {
    const root = tableShellRef.current;
    const sticky = stickyScrollRef.current;
    if (!root || !sticky) return undefined;
    const scrollEl = root.querySelector<HTMLElement>('.ant-table-content, .ant-table-body');
    if (!scrollEl) return undefined;

    const updateWidth = () => {
      setStickyScrollWidth(Math.max(scrollEl.scrollWidth, scrollEl.clientWidth, CASE_TABLE_SCROLL_WIDTH));
    };

    let syncing = false;
    const syncSticky = () => {
      if (syncing) return;
      syncing = true;
      sticky.scrollLeft = scrollEl.scrollLeft;
      syncing = false;
    };
    const syncTable = () => {
      if (syncing) return;
      syncing = true;
      scrollEl.scrollLeft = sticky.scrollLeft;
      syncing = false;
    };

    scrollEl.addEventListener('scroll', syncSticky, { passive: true });
    sticky.addEventListener('scroll', syncTable, { passive: true });

    const observer = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(updateWidth) : null;
    observer?.observe(scrollEl);
    observer?.observe(root);
    updateWidth();
    syncSticky();

    return () => {
      scrollEl.removeEventListener('scroll', syncSticky);
      sticky.removeEventListener('scroll', syncTable);
      observer?.disconnect();
    };
  }, [rows, loading, shadowLoading]);

  async function refreshCases(showLoading: boolean = true) {
    await loadCases(showLoading);
  }

  async function handleCreateCase(values: NewCaseFormValues) {
    setCreating(true);
    setMessage('');
    setCreatedCaseId('');
    try {
      const patient = await createPatient({
        external_patient_id: values.external_patient_id || undefined,
        display_name: values.display_name || values.external_patient_id || '新建患者',
        sex: values.sex || undefined,
        consent_status: 'unknown',
      });
      const createdCase = await createCase({
        patient_id: patient.patient_id,
        case_no: values.case_no || undefined,
        disease_task: values.disease_task || 'cap_cop',
        status: 'open',
        chief_complaint: values.chief_complaint || undefined,
      });
      setMessageType('success');
      setMessage('病例已创建：' + (createdCase.case_no || createdCase.case_id));
      setCreatedCaseId(createdCase.case_id);
      form.resetFields();
      await refreshCases();
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeCaseError(error));
    } finally {
      setCreating(false);
    }
  }

  return (
    <Space direction='vertical' style={{ width: '100%' }} size={16}>
      <Typography.Title level={4} style={{ margin: 0 }}>患者病例列表</Typography.Title>
      <Alert
        type='info'
        showIcon
        message='病例用于本地工作流验证'
        description='新增病例只创建病例对象，不会触发模型运行，也不会写推荐结果或病例溯源证据。36 个 CAP/COP clinical MLP 特征属于模型输入快照，不属于病例基础字段；请进入病例详情的“CAP/COP 特征与输入快照”页面查看特征映射与校验。当前页面不是完整手工录入表，后续如要逐项录入 36 个字段，需要单独的 case_model_input_snapshot 编辑表单。'
      />
      <Card size='small' title='相关疾病属性说明'>
        <Space direction='vertical' size={4}>
          <Typography.Text>病例基础信息只创建病例对象。</Typography.Text>
          <Typography.Text>36 个 CAP/COP clinical MLP 特征属于模型输入快照，不属于病例基础字段。</Typography.Text>
          <Typography.Text>请进入病例详情的“CAP/COP 特征与输入快照”页面查看特征映射、缺失项和校验状态。</Typography.Text>
          <Typography.Text>当前页面是特征映射与校验，不是完整手工录入表；如要逐项录入 36 个字段，需要后续单独补 case_model_input_snapshot 编辑表单。</Typography.Text>
          <Typography.Text>如果缺 required feature，需要走缺失值咨询 / 明确默认策略 / insufficient_data_for_assessment，不能 silent fallback。</Typography.Text>
          <Typography.Text>只有存在可推理状态的输入快照，并执行受控 shadow，病例列表才会出现 CAP/COP shadow 摘要。</Typography.Text>
        </Space>
      </Card>
      {message ? (
        <Alert
          type={messageType}
          showIcon
          message={message}
          description={messageType === 'success' && createdCaseId ? (
            <Space wrap size={8}>
              <Link href={'/cases/' + createdCaseId + '/model-input'}>填写/校验 CAP-COP 特征</Link>
              <Link href={'/cases/' + createdCaseId + '/shadow-audit'}>查看 Shadow 审计</Link>
            </Space>
          ) : null}
        />
      ) : null}

      <Card title='新增病例'>
        <Form form={form} layout='vertical' onFinish={handleCreateCase} initialValues={{ disease_task: 'cap_cop' }}>
          <Space size={16} wrap align='start' style={{ width: '100%' }}>
            <Form.Item label='患者显示名' name='display_name' rules={[{ required: true, message: '请输入患者显示名' }]} style={{ minWidth: 220 }}>
              <Input placeholder='例如：测试患者 A' />
            </Form.Item>
            <Form.Item label='外部患者号' name='external_patient_id' style={{ minWidth: 220 }}>
              <Input placeholder='可选，例如：DEV-PAT-001' />
            </Form.Item>
            <Form.Item label='性别' name='sex' style={{ minWidth: 160 }}>
              <Select allowClear options={[{ label: '男', value: 'male' }, { label: '女', value: 'female' }, { label: '未知', value: 'unknown' }]} />
            </Form.Item>
            <Form.Item label='病例编号' name='case_no' style={{ minWidth: 220 }}>
              <Input placeholder='可选，留空自动生成' />
            </Form.Item>
            <Form.Item label='病种任务' name='disease_task' rules={[{ required: true, message: '请选择病种任务' }]} style={{ minWidth: 180 }}>
              <Select options={[{ label: 'CAP/COP', value: 'cap_cop' }, { label: '未指定', value: 'UNSPECIFIED' }]} />
            </Form.Item>
            <Form.Item label='主诉/备注' name='chief_complaint' style={{ minWidth: 360 }}>
              <Input.TextArea rows={3} placeholder='用于本地验证的病例上下文，可留空' />
            </Form.Item>
          </Space>
          <Button type='primary' htmlType='submit' loading={creating}>新增病例</Button>
        </Form>
      </Card>

      <Card title='病例列表'>
        <div ref={tableShellRef}>
          <Table
            rowKey='key'
            loading={loading || shadowLoading}
            dataSource={rows}
            pagination={false}
            scroll={{ x: CASE_TABLE_SCROLL_WIDTH }}
            columns={[
              { title: '病例 ID', dataIndex: 'case_id', width: 220, render: (value: string) => value || '-' },
              { title: '患者姓名 / 显示名', dataIndex: 'patient_display_name', width: 220, render: (value: string) => value || '-' },
              { title: '病例编号', dataIndex: 'case_no', width: 180, render: (value: string) => value || '-' },
              { title: '患者 ID', dataIndex: 'patient_id', width: 240, render: (value: string) => value || '-' },
              { title: '病种任务', dataIndex: 'disease_task', width: 140, render: (value: string) => <Tag>{getDiseaseTaskLabel(value)}</Tag> },
              { title: '状态', dataIndex: 'status', width: 120, render: (value: string) => <Tag>{getCaseStatusLabel(value)}</Tag> },
              {
                title: 'Trace / 溯源',
                dataIndex: 'trace_id',
                width: 220,
                render: (value: string, row: CaseRow) => value ? <Space direction='vertical' size={2}>
                  <Typography.Text>{value}</Typography.Text>
                  <Link href={'/cases/' + row.case_id + '/lineage' + (value ? '?trace_id=' + value : '')}>查看溯源</Link>
                </Space> : '-',
              },
              {
                title: 'CAP/COP Shadow 审计',
                width: 340,
                render: (_: unknown, row: CaseRow) => <ShadowCell caseId={row.case_id} summary={shadowSummaries[row.case_id]} />,
              },
              {
                title: '操作',
                width: 540,
                render: (_: unknown, row: CaseRow) => row.case_id ? <Space wrap>
                  <Link href={'/cases/' + row.case_id + '/multimodal'}>多模态数据</Link>
                  <Link href={'/cases/' + row.case_id + '/model-input'}>CAP/COP 特征与输入快照</Link>
                  <Link href={'/cases/' + row.case_id + '/missing-consultation'}>缺失值确认</Link>
                  <Link href={'/cases/' + row.case_id + '/small-models'}>小模型分析</Link>
                  <Link href={'/cases/' + row.case_id + '/shadow-audit'}>Shadow 审计</Link>
                  <Link href={'/cases/' + row.case_id + '/lineage'}>查看溯源</Link>
                  <Link href={'/cases/' + row.case_id + '/feedback'}>反馈</Link>
                </Space> : '-'
              }
            ]}
          />
        </div>
        <div
          style={{
            position: 'sticky',
            bottom: 0,
            zIndex: 2,
            marginTop: 8,
            borderTop: '1px solid #f0f0f0',
            background: 'rgba(255, 255, 255, 0.96)',
            backdropFilter: 'blur(8px)',
            boxShadow: '0 -1px 0 rgba(0, 0, 0, 0.02)',
          }}
        >
          <div
            ref={stickyScrollRef}
            style={{
              overflowX: 'auto',
              overflowY: 'hidden',
              height: 16,
            }}
            aria-label='病例列表横向滚动条'
          >
            <div style={{ width: stickyScrollWidth, height: 1 }} />
          </div>
        </div>
      </Card>
    </Space>
  );
}
