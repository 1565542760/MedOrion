'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Alert, Button, Card, Form, Input, Select, Space, Table, Tag, Typography } from 'antd';
import { createCase, createPatient, listCases, type CaseItem } from '@/lib/api';

type CaseRow = CaseItem & { key?: string };

type NewCaseFormValues = {
  external_patient_id?: string;
  display_name?: string;
  sex?: string;
  case_no?: string;
  disease_task?: string;
  chief_complaint?: string;
};

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

export default function CasesPage() {
  const [form] = Form.useForm<NewCaseFormValues>();
  const [rows, setRows] = useState<CaseRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'info' | 'warning' | 'error'>('info');

  async function refreshCases(showLoading: boolean = true) {
    if (showLoading) setLoading(true);
    try {
      const data = await listCases();
      const normalized = Array.isArray(data)
        ? (data as CaseRow[]).map((row) => ({ ...row, key: makeCaseKey(row) }))
        : [];
      setRows(normalized);
    } catch {
      setRows([]);
      setMessageType('error');
      setMessage('病例列表加载失败，请确认后端服务和登录状态。');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    listCases()
      .then((data) => {
        if (!active) return;
        const normalized = Array.isArray(data)
          ? (data as CaseRow[]).map((row) => ({ ...row, key: makeCaseKey(row) }))
          : [];
        setRows(normalized);
      })
      .catch(() => {
        if (!active) return;
        setRows([]);
        setMessageType('error');
        setMessage('病例列表加载失败，请确认后端服务和登录状态。');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleCreateCase(values: NewCaseFormValues) {
    setCreating(true);
    setMessage('');
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
        description='新增病例会先创建一个最小患者记录，再创建病例记录；不会触发模型运行、不会写 recommendation，也不会写病例 trace/evidence。'
      />
      {message ? <Alert type={messageType} showIcon message={message} /> : null}

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
        <Table
          rowKey='key'
          loading={loading}
          dataSource={rows}
          pagination={false}
          scroll={{ x: 1300 }}
          columns={[
            { title: 'Case ID', dataIndex: 'case_id', width: 240, render: (value: string) => value || '-' },
            { title: 'Case No', dataIndex: 'case_no', width: 180, render: (value: string) => value || '-' },
            { title: 'Patient ID', dataIndex: 'patient_id', width: 240, render: (value: string) => value || '-' },
            { title: 'Task', dataIndex: 'disease_task', width: 140, render: (value: string) => <Tag>{value || '-'}</Tag> },
            { title: 'Status', dataIndex: 'status', width: 120, render: (value: string) => value || '-' },
            { title: 'Trace', dataIndex: 'trace_id', width: 200, render: (value: string) => value || '-' },
            {
              title: '操作',
              width: 520,
              render: (_: unknown, row: CaseRow) => row.case_id ? <Space wrap>
                <Link href={'/cases/' + row.case_id + '/multimodal'}>多模态数据</Link>
                <Link href={'/cases/' + row.case_id + '/model-input'}>模型输入</Link>
                <Link href={'/cases/' + row.case_id + '/missing-consultation'}>缺失值确认</Link>
                <Link href={'/cases/' + row.case_id + '/small-models'}>小模型分析</Link>
                <Link href={'/cases/' + row.case_id + '/shadow-audit'}>Shadow 审计</Link>
                <Link href={'/cases/' + row.case_id + '/lineage'}>查看溯源</Link>
                <Link href={'/cases/' + row.case_id + '/feedback'}>反馈</Link>
              </Space> : '-'
            }
          ]}
        />
      </Card>
    </Space>
  );
}
