'use client';

import axios from 'axios';
import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Form, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
import {
  createCase,
  createPatient,
  getCapCopShadowWorkflowReadiness,
  listCaseImagingInputs,
  listCases,
  listModelInputSnapshotsByCase,
  listPatients,
  listShadowRunsByCase,
  type CaseItem,
} from '@/lib/api';

type CaseRow = CaseItem & {
  key: string;
  patient_name: string;
  patient_identifier: string;
  sex?: string | null;
  clinical_status: string;
  imaging_status: string;
  workflow_status: string;
  latest_result: string;
  next_action: string;
};

type NewCaseFormValues = {
  external_patient_id?: string;
  display_name?: string;
  sex?: string;
  case_no?: string;
  disease_task?: string;
  chief_complaint?: string;
};

function diseaseLabel(value?: string | null) {
  if (!value) return '-';
  if (value === 'cap_cop') return 'CAP/COP';
  return value;
}

function caseStatus(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'open': return '进行中';
    case 'closed': return '已关闭';
    case 'archived': return '已归档';
    case 'draft': return '草稿';
    default: return value || '-';
  }
}

function sexLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'male': return '男';
    case 'female': return '女';
    default: return value || '-';
  }
}

function workflowLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'ready_all': return '全部可评估';
    case 'ready_partial': return '部分可评估';
    case 'blocked': return '暂不可评估';
    default: return value || '待评估';
  }
}

function nextAction(row: { clinical: number; imaging: number; workflow?: string | null }) {
  if (row.clinical === 0) return '补临床输入';
  if (row.imaging === 0) return '处理影像';
  if ((row.workflow || '').toLowerCase() === 'blocked') return '查看缺口';
  return '模型评估';
}

function actionHref(caseId: string, action: string) {
  if (action === '补临床输入') return '/cases/' + caseId + '/model-input';
  if (action === '处理影像') return '/cases/' + caseId + '/imaging-inputs';
  if (action === '模型评估') return '/cases/' + caseId + '/model-workflow';
  return '/cases/' + caseId;
}


function getCreateCaseErrorMessage(error: unknown) {
  if (!axios.isAxiosError(error)) return '创建失败，请稍后重试。';
  const status = error.response?.status;
  const code = (error.response?.data as { code?: string } | undefined)?.code;
  if (code === 'invalid_consent_status') return '患者信息填写不符合系统要求。';
  if (code === 'patient_conflict') return '患者ID已存在。';
  if (code === 'case_conflict') return '病例编号已存在。';
  if (status === 422) return '提交信息校验未通过。';
  if (status === 409) return '存在重复记录。';
  return '创建失败，请稍后重试。';
}

export default function CasesPage() {
  const [form] = Form.useForm<NewCaseFormValues>();
  const [rows, setRows] = useState<CaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const loadCases = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      const [caseData, patientData] = await Promise.all([listCases(), listPatients()]);
      const patientMap = new Map(patientData.map((item) => [item.patient_id, item]));
      const summaries = await Promise.all((caseData || []).map(async (item) => {
        const [snapshots, images, runs, readiness] = await Promise.allSettled([
          listModelInputSnapshotsByCase(item.case_id),
          listCaseImagingInputs(item.case_id),
          listShadowRunsByCase(item.case_id),
          getCapCopShadowWorkflowReadiness(item.case_id),
        ]);
        const patient = patientMap.get(item.patient_id);
        const clinical = snapshots.status === 'fulfilled' ? snapshots.value.items.length : 0;
        const imaging = images.status === 'fulfilled' ? images.value.items.length : 0;
        const latestRun = runs.status === 'fulfilled' ? [...(runs.value.items || [])].sort((a, b) => new Date(b.started_at || b.created_at || 0).getTime() - new Date(a.started_at || a.created_at || 0).getTime())[0] : null;
        const workflow = readiness.status === 'fulfilled' ? readiness.value.overall_status || 'blocked' : 'blocked';
        const action = nextAction({ clinical, imaging, workflow });
        return {
          ...item,
          key: item.case_id,
          patient_name: patient?.display_name || patient?.external_patient_id || item.patient_id,
          patient_identifier: patient?.external_patient_id || item.patient_id,
          sex: patient?.sex || null,
          clinical_status: clinical > 0 ? '已建输入快照' : '待补临床输入',
          imaging_status: imaging > 0 ? '已有影像输入' : '待登记影像',
          workflow_status: workflowLabel(workflow),
          latest_result: latestRun?.status || '暂无',
          next_action: action,
        } as CaseRow;
      }));
      setRows(summaries);
    } catch (error) {
      setMessage(getCreateCaseErrorMessage(error));
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void loadCases(); }, 0);
    return () => window.clearTimeout(timer);
  }, [loadCases]);

  async function handleCreate(values: NewCaseFormValues) {
    setCreating(true);
    try {
      const patient = await createPatient({
        external_patient_id: values.external_patient_id || undefined,
        display_name: values.display_name || undefined,
        name: values.display_name || undefined,
        sex: values.sex || undefined,
        consent_status: 'unknown',
      });
      await createCase({
        patient_id: patient.patient_id,
        case_no: values.case_no || undefined,
        disease_task: values.disease_task || 'cap_cop',
        status: 'open',
        chief_complaint: values.chief_complaint || undefined,
      });
      setModalOpen(false);
      form.resetFields();
      await loadCases();
    } catch (error) {
      setMessage(getCreateCaseErrorMessage(error));
    } finally {
      setCreating(false);
    }
  }

  const filteredRows = useMemo(() => {
    const text = query.trim().toLowerCase();
    return rows.filter((row) => {
      const haystack = [row.patient_name, row.patient_identifier, row.case_no, row.case_id, row.clinical_status, row.imaging_status, row.workflow_status].join(' ').toLowerCase();
      const textOk = !text || haystack.includes(text);
      const statusOk = statusFilter === 'all'
        || (statusFilter === 'clinical_missing' && row.clinical_status.includes('待补'))
        || (statusFilter === 'imaging_pending' && row.imaging_status.includes('待登记'))
        || (statusFilter === 'ready_for_model' && row.workflow_status.includes('可评估'))
        || (statusFilter === 'failed' && row.latest_result.toLowerCase().includes('failed'));
      return textOk && statusOk;
    });
  }, [query, rows, statusFilter]);

  const columns = [
    { title: '姓名', dataIndex: 'patient_name', width: 150, fixed: 'left' as const, render: (value: string, row: CaseRow) => <Link href={'/cases/' + row.case_id}>{value}</Link> },
    { title: '患者ID', dataIndex: 'patient_identifier', width: 190, fixed: 'left' as const },
    { title: '住院/门诊号', dataIndex: 'case_no', width: 150, render: (value: string | null) => value || '-' },
    { title: '年龄', width: 80, render: () => '-' },
    { title: '性别', dataIndex: 'sex', width: 80, render: sexLabel },
    { title: '科室/病区', width: 120, render: () => '-' },
    { title: '任务', dataIndex: 'disease_task', width: 110, render: diseaseLabel },
    { title: '病例状态', dataIndex: 'status', width: 110, render: caseStatus },
    { title: '临床输入', dataIndex: 'clinical_status', width: 150, render: (value: string) => <Tag color={value.includes('已') ? 'green' : 'gold'}>{value}</Tag> },
    { title: '影像预处理', dataIndex: 'imaging_status', width: 150, render: (value: string) => <Tag color={value.includes('已有') ? 'green' : 'gold'}>{value}</Tag> },
    { title: '模型评估', dataIndex: 'workflow_status', width: 140, render: (value: string) => <Tag color={value.includes('全部') || value.includes('部分') ? 'blue' : 'default'}>{value}</Tag> },
    { title: '最近结果', dataIndex: 'latest_result', width: 130 },
    { title: '下一步', dataIndex: 'next_action', width: 140, render: (value: string, row: CaseRow) => <Button size='small' href={actionHref(row.case_id, value)}>{value}</Button> },
    { title: '操作', width: 150, fixed: 'right' as const, render: (_: unknown, row: CaseRow) => <Space><Link href={'/cases/' + row.case_id}>概览</Link><Link href={'/cases/' + row.case_id + '/shadow-audit'}>审计</Link></Space> },
  ];

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <Space direction='vertical' size={2}>
          <Typography.Title level={3} style={{ margin: 0 }}>患者/病例</Typography.Title>
          <Typography.Text type='secondary'>按院内身份信息查找患者，进入病例后再完成临床输入、影像和模型评估。</Typography.Text>
        </Space>
        <Button type='primary' onClick={() => setModalOpen(true)}>登记新病例</Button>
      </div>
      {message ? <Alert type='error' showIcon message={message} /> : null}
      <WorkspaceTableShell
        title='患者病例工作列表'
        subtitle='表格窗口内可横向滚动，姓名和患者ID固定在左侧。'
        actions={
          <Space wrap>
            <Input.Search allowClear placeholder='搜索姓名、患者ID、住院号' onSearch={setQuery} onChange={(event) => setQuery(event.target.value)} style={{ width: 260 }} />
            <Select value={statusFilter} onChange={setStatusFilter} style={{ width: 180 }} options={[
              { value: 'all', label: '全部' },
              { value: 'clinical_missing', label: '待临床输入' },
              { value: 'imaging_pending', label: '待影像预处理' },
              { value: 'ready_for_model', label: '可模型评估' },
              { value: 'failed', label: '失败任务' },
            ]} />
            <Button onClick={loadCases}>刷新</Button>
          </Space>
        }
      >
        <Table rowKey='case_id' loading={loading} columns={columns} dataSource={filteredRows} pagination={false} sticky scroll={{ x: 1880, y: 'calc(100vh - 360px)' }} size='middle' />
      </WorkspaceTableShell>

      <Modal title='登记新病例' open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} confirmLoading={creating} okText='保存' cancelText='取消' destroyOnHidden>
        <Form form={form} layout='vertical' onFinish={handleCreate} initialValues={{ disease_task: 'cap_cop', sex: 'unknown' }}>
          <Form.Item label='患者姓名' name='display_name' rules={[{ required: true, message: '请输入患者姓名' }]}><Input /></Form.Item>
          <Form.Item label='患者ID' name='external_patient_id' rules={[{ required: true, message: '请输入患者ID' }]}><Input /></Form.Item>
          <Form.Item label='性别' name='sex'><Select options={[{ value: 'male', label: '男' }, { value: 'female', label: '女' }, { value: 'unknown', label: '未知' }]} /></Form.Item>
          <Form.Item label='住院/门诊号' name='case_no'><Input /></Form.Item>
          <Form.Item label='任务' name='disease_task'><Select options={[{ value: 'cap_cop', label: 'CAP/COP' }]} /></Form.Item>
          <Form.Item label='主诉/备注' name='chief_complaint'><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
