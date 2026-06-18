'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Alert, Button, Descriptions, Drawer, Form, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd';
import { CaseSubNav } from '@/components/CaseSubNav';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
import {
  formatApiErrorMessage,
  getImagingPreprocessingStatus,
  type ImagingPreprocessResponse,
  listCaseImagingInputs,
  listCases,
  listPatients,
  registerDicomSeries,
  requestImagingPreprocess,
  uploadDicomSeriesFiles,
  type CaseImagingInputItem,
  type CaseItem,
  type DicomSeriesRegisterPayload,
  type ImagingPreprocessingStatusResponse,
  type PatientItem,
} from '@/lib/api';

type DicomFormValues = { series_label?: string; source_type?: string; dicom_series_ref?: string; storage_uri?: string };
type DicomUploadValues = { modality?: string; source_type?: string };

function patientName(patient: PatientItem | null) {
  return patient?.display_name || patient?.external_patient_id || '未命名患者';
}

function patientId(patient: PatientItem | null, caseItem: CaseItem | null) {
  return patient?.external_patient_id || caseItem?.patient_id || '-';
}

function sourceLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'dicom_series': return '登记影像序列（DICOM）';
    case 'real_deidentified': return '真实脱敏影像';
    case 'synthetic': return '合成/演示影像';
    case 'demo': return '演示数据';
    default: return value || '-';
  }
}

function workflowStatusLabel(row: CaseImagingInputItem, status?: ImagingPreprocessingStatusResponse) {
  const preprocessingStatus = (status?.preprocessing_status || '').toLowerCase();
  const responseStatus = (status?.status || '').toLowerCase();
  const uploadState = String((status?.provenance_json as Record<string, unknown> | undefined)?.upload_state || (row.provenance_json as Record<string, unknown> | undefined)?.upload_state || '').toLowerCase();
  if (preprocessingStatus === 'completed' || responseStatus === 'completed') return '预处理完成，可运行';
  if (preprocessingStatus === 'failed' || responseStatus === 'failed') return '预处理失败';
  if (preprocessingStatus === 'running' || preprocessingStatus === 'processing' || responseStatus === 'running' || responseStatus === 'processing') return '真实执行中';
  if (preprocessingStatus === 'planned' || preprocessingStatus === 'ready_for_preprocessing' || responseStatus === 'planned' || responseStatus === 'ready_for_preprocessing') return '预处理计划已生成，等待执行';
  if (preprocessingStatus === 'not_implemented' || responseStatus === 'not_implemented') return '预处理契约未实现';
  if (uploadState === 'uploaded_to_controlled_storage') return '已上传，等待预处理';
  return '待处理';
}

function workflowStatusColor(label: string) {
  if (label.includes('完成') || label.includes('可运行')) return 'green';
  if (label.includes('失败')) return 'red';
  if (label.includes('未实现') || label.includes('待')) return 'gold';
  return 'blue';
}

function uploadManifestSummary(status?: ImagingPreprocessingStatusResponse) {
  const provenance = status?.provenance_json as { upload_manifest?: Array<{ filename?: string }> } | undefined;
  const manifest = provenance?.upload_manifest || [];
  if (!manifest.length) return '-';
  return manifest.slice(0, 4).map((item) => item.filename || '-').join('、') + (manifest.length > 4 ? ' 等' : '');
}
export default function ImagingInputsPage() {
  const pathname = usePathname();
  const caseId = useMemo(() => pathname.match(/^\/cases\/([^/]+)/)?.[1] || '', [pathname]);
  const [registerForm] = Form.useForm<DicomFormValues>();
  const [uploadForm] = Form.useForm<DicomUploadValues>();
  const [caseItem, setCaseItem] = useState<CaseItem | null>(null);
  const [patient, setPatient] = useState<PatientItem | null>(null);
  const [items, setItems] = useState<CaseImagingInputItem[]>([]);
  const [statuses, setStatuses] = useState<Record<string, ImagingPreprocessingStatusResponse>>({});
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState('');
  const [message, setMessage] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadTraceId, setUploadTraceId] = useState('');
  const [uploadStage, setUploadStage] = useState('');
  const [detail, setDetail] = useState<CaseImagingInputItem | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setMessage('');
    try {
      const imaging = await listCaseImagingInputs(caseId);
      const rows = (imaging.items || []) as CaseImagingInputItem[];
      setItems(rows);

      const [casesResult, patientsResult] = await Promise.allSettled([listCases(), listPatients()]);
      const foundCases = casesResult.status === 'fulfilled' ? casesResult.value : [];
      const foundPatients = patientsResult.status === 'fulfilled' ? patientsResult.value : [];
      const firstRow = rows[0] || null;
      const foundCase = (foundCases || []).find((item: CaseItem) => item.case_id === caseId) || (firstRow ? { case_id: caseId, patient_id: firstRow.patient_id || '', case_no: null, disease_task: 'cap_cop', status: 'open', trace_id: firstRow.trace_id || null } as CaseItem : null);
      setCaseItem(foundCase);
      const resolvedPatientId = foundCase?.patient_id || firstRow?.patient_id || '';
      setPatient((foundPatients || []).find((item: PatientItem) => item.patient_id === resolvedPatientId) || null);

      const pairs = await Promise.all(rows.map(async (row) => {
        try { return [row.input_asset_id, await getImagingPreprocessingStatus(row.input_asset_id)] as const; } catch { return [row.input_asset_id, null] as const; }
      }));
      setStatuses(Object.fromEntries(pairs.filter(([, value]) => !!value)) as Record<string, ImagingPreprocessingStatusResponse>);
    } catch {
      setMessage('影像输入页加载失败，请稍后重试。');
      setItems([]);
      setStatuses({});
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  function openUpload() {
    const traceId = caseItem?.trace_id || (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : 'trace-' + Date.now().toString(36));
    setUploadTraceId(traceId);
    uploadForm.setFieldsValue({ modality: 'CT', source_type: 'real_deidentified' });
    setUploadFiles([]);
    setUploadStage('');
    setUploadOpen(true);
  }

  function openRegister() {
    registerForm.setFieldsValue({ source_type: 'dicom_series', series_label: 'DICOM 影像序列', dicom_series_ref: '', storage_uri: '' });
    setRegisterOpen(true);
  }

  async function handleUpload(values: DicomUploadValues) {
    const resolvedPatientId = caseItem?.patient_id || patient?.patient_id || '';
    if (!resolvedPatientId) return setMessage('当前病例未关联患者，无法上传影像。');
    if (!uploadFiles.length) return setMessage('请先选择一组 DICOM 文件。');
    const traceId = uploadTraceId || caseItem?.trace_id || (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : 'trace-' + Date.now().toString(36));
    setUploading(true);
    setMessage('正在上传 DICOM 文件集合，请稍候。');
    setUploadStage('正在上传 DICOM 文件集合');
    try {
      await uploadDicomSeriesFiles(caseId, {
        patient_id: resolvedPatientId,
        trace_id: traceId,
        files: uploadFiles,
        modality: values.modality || 'CT',
        source_type: values.source_type || 'real_deidentified',
        deidentified: true,
        not_for_diagnosis: true,
      });
      setUploadOpen(false);
      uploadForm.resetFields();
      setUploadFiles([]);
      setMessage('已接收 ' + uploadFiles.length + ' 个 DICOM 文件，系统将进入受控预处理流程。');
      await load();
    } catch (error) {
      setMessage(formatApiErrorMessage(error, 'DICOM 文件上传失败，请稍后重试。'));
    } finally {
      setUploading(false);
    }
  }

  async function handleRegister(values: DicomFormValues) {
    const payload: DicomSeriesRegisterPayload = {
      series_label: values.series_label || 'DICOM 影像序列',
      source_type: values.source_type || 'dicom_series',
      dicom_series_ref: values.dicom_series_ref || values.storage_uri || '',
      storage_uri: values.storage_uri || values.dicom_series_ref || '',
      deidentified: true,
      not_for_diagnosis: true,
      provenance_json: { registered_from: 'doctor_workstation' },
      quality_flags_json: { preprocessing_status: 'pending' },
    };
    if (!payload.dicom_series_ref) return setMessage('请填写 DICOM 引用或存储位置。');
    try {
      await registerDicomSeries(caseId, payload);
      setRegisterOpen(false);
      registerForm.resetFields();
      await load();
      setMessage('影像序列已登记，列表已刷新。');
    } catch (error) {
      setMessage(formatApiErrorMessage(error, '登记影像序列失败，请稍后重试。'));
    }
  }

  async function handlePreprocess(inputAssetId: string) {
    setBusyId(inputAssetId);
    setMessage('正在请求预处理，请稍候。');
    let nextMessage = '请求预处理已提交，正在刷新状态。';
    try {
      const result = (await requestImagingPreprocess(inputAssetId)) as ImagingPreprocessResponse;
      const refreshed = await getImagingPreprocessingStatus(inputAssetId).catch(() => null);
      const status = String(refreshed?.preprocessing_status || result.preprocessing_status || result.status || '').toLowerCase();
      if (status === 'completed') {
        nextMessage = '真实执行成功：预处理完成，可运行。';
      } else if (status === 'failed') {
        nextMessage = '真实执行失败，请查看详情原因。';
      } else if (status === 'running' || status === 'processing') {
        nextMessage = '真实执行中，请稍候。';
      } else if (status === 'planned' || status === 'ready_for_preprocessing') {
        nextMessage = '预处理计划已生成，等待真实执行。';
      } else if (status === 'not_implemented') {
        nextMessage = '预处理契约未实现。';
      } else if (result.message) {
        nextMessage = '预处理已受理，系统正在刷新状态。';
      }
      if (refreshed && refreshed.input_asset_id) {
        setStatuses((current) => ({ ...current, [refreshed.input_asset_id]: refreshed }));
        setItems((current) => current.map((item) => item.input_asset_id === refreshed.input_asset_id ? { ...item, storage_uri: refreshed.storage_uri || item.storage_uri, source_type: refreshed.source_type || item.source_type, deidentified: refreshed.deidentified ?? item.deidentified, not_for_diagnosis: refreshed.not_for_diagnosis ?? item.not_for_diagnosis } : item));
      }
    } catch (error) {
      nextMessage = formatApiErrorMessage(error, '请求预处理失败，请稍后重试。');
    } finally {
      await load();
      setBusyId('');
      setMessage(nextMessage);
    }
  }

  const uploadSummary = useMemo(() => {
    if (!uploadFiles.length) return '尚未选择文件';
    const names = uploadFiles.slice(0, 4).map((file) => file.name).join('、');
    return '已选择 ' + uploadFiles.length + ' 个文件：' + names + (uploadFiles.length > 4 ? ' 等' : '');
  }, [uploadFiles]);

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%' }}>
      <CaseSubNav caseId={caseId} patientName={patientName(patient)} patientId={patientId(patient, caseItem)} caseNo={caseItem?.case_no} />
      {message ? <Alert type='warning' showIcon message={message} /> : null}
      <Alert type='info' showIcon message='这里支持两种影像输入方式：上传同一患者的一组 DICOM 文件，或者登记影像序列引用。上传后会进入受控预处理流程，生成 image.nii.gz 后才能进入影像模型评估。' />

      <WorkspaceTableShell
        title='影像输入 / 数字孪生'
        subtitle='这里记录影像输入、预处理状态和病例级影像契约，不直接展示诊断结论。'
        actions={<Space><Button type='primary' onClick={openUpload}>上传 DICOM 文件集合</Button><Button onClick={openRegister}>登记影像序列（引用）</Button><Button onClick={load}>刷新</Button></Space>}
      >
        <Table
          rowKey='input_asset_id'
          loading={loading}
          dataSource={items}
          pagination={false}
          sticky
          scroll={{ x: 1560, y: 'calc(100vh - 340px)' }}
          columns={[
            { title: '影像输入 ID', dataIndex: 'input_asset_id', width: 220, fixed: 'left' as const },
            { title: '来源类型', dataIndex: 'source_type', width: 180, render: sourceLabel },
            { title: '预处理状态', width: 180, render: (_: unknown, row: CaseImagingInputItem) => <Tag color={workflowStatusColor(workflowStatusLabel(row, statuses[row.input_asset_id]))}>{workflowStatusLabel(row, statuses[row.input_asset_id])}</Tag> },
            { title: 'DICOM 影像引用', dataIndex: 'storage_uri', width: 360, ellipsis: true },
            { title: '模型输入文件', width: 360, render: (_: unknown, row: CaseImagingInputItem) => statuses[row.input_asset_id]?.model_input_file || row.storage_uri || '-' },
            { title: '脱敏', dataIndex: 'deidentified', width: 100, render: (value: boolean) => <Tag color={value ? 'green' : 'gold'}>{value ? '是' : '否'}</Tag> },
            { title: '非诊断', dataIndex: 'not_for_diagnosis', width: 100, render: (value: boolean) => <Tag color={value ? 'green' : 'gold'}>{value ? '是' : '否'}</Tag> },
            { title: '操作', width: 220, fixed: 'right' as const, render: (_: unknown, row: CaseImagingInputItem) => <Space><Button size='small' onClick={() => setDetail(row)}>查看</Button><Button size='small' loading={busyId === row.input_asset_id} onClick={() => handlePreprocess(row.input_asset_id)}>请求预处理</Button></Space> },
          ]}
        />
      </WorkspaceTableShell>

      <Modal title='上传 DICOM 文件集合' open={uploadOpen} onCancel={() => setUploadOpen(false)} onOk={() => uploadForm.submit()} okText='上传并登记' cancelText='取消' confirmLoading={uploading} destroyOnHidden>
        <Form form={uploadForm} layout='vertical' onFinish={handleUpload} initialValues={{ modality: 'CT', source_type: 'real_deidentified' }}>
          <div style={{ marginBottom: 12 }}>
            <Typography.Text type='secondary'>系统溯源编号（自动生成）：{uploadTraceId || caseItem?.trace_id || '-'}</Typography.Text>
          </div>
          <Form.Item label='模态' name='modality'><Select options={[{ value: 'CT', label: 'CT' }, { value: 'XRAY', label: 'X 线' }, { value: 'MRI', label: 'MRI' }, { value: 'US', label: '超声' }]} /></Form.Item>
          <Form.Item label='来源类型' name='source_type'><Select options={[{ value: 'real_deidentified', label: '真实脱敏' }, { value: 'synthetic', label: '合成/演示' }, { value: 'demo', label: '演示数据' }]} /></Form.Item>
          <Form.Item label='DICOM 文件集合' required>
            <div style={{ border: '1px dashed #d9d9d9', borderRadius: 8, padding: 12, background: '#fafafa' }}>
              <input type='file' multiple accept='.dcm,.dicom,.ima,application/dicom' onChange={(event) => setUploadFiles(Array.from(event.target.files || []))} style={{ width: '100%' }} />
              <Typography.Text type='secondary' style={{ display: 'block', marginTop: 8 }}>请选择同一患者的一组 DICOM 序列文件。系统会接收并交由服务器做受控存储与预处理。</Typography.Text>
              <Typography.Text style={{ display: 'block', marginTop: 8 }}>{uploadSummary}</Typography.Text>
            <Typography.Text type='secondary' style={{ display: 'block', marginTop: 8 }}>{uploading ? uploadStage || '正在上传 DICOM 文件集合' : '上传后将自动登记影像序列，并等待预处理完成。'}</Typography.Text>
            </div>
          </Form.Item>
          <Space wrap>
            <Tag color='green'>脱敏后使用</Tag>
            <Tag color='green'>非诊断用途</Tag>
          </Space>
        </Form>
      </Modal>

      <Modal title='登记影像序列（引用）' open={registerOpen} onCancel={() => setRegisterOpen(false)} onOk={() => registerForm.submit()} okText='保存' cancelText='取消' destroyOnHidden>
        <Form form={registerForm} layout='vertical' onFinish={handleRegister} initialValues={{ source_type: 'dicom_series', series_label: 'DICOM 影像序列' }}>
          <Form.Item label='序列名称' name='series_label'><Input /></Form.Item>
          <Form.Item label='来源类型' name='source_type'><Select options={[{ value: 'dicom_series', label: '登记影像序列（DICOM）' }, { value: 'synthetic', label: '合成/演示影像' }, { value: 'demo', label: '演示数据' }]} /></Form.Item>
          <Form.Item label='DICOM 引用' name='dicom_series_ref' rules={[{ required: true, message: '请填写 DICOM 引用' }]}><Input placeholder='managed://...' /></Form.Item>
          <Form.Item label='存储位置' name='storage_uri'><Input placeholder='managed://...' /></Form.Item>
          <Space wrap>
            <Tag color='green'>脱敏后使用</Tag>
            <Tag color='green'>非诊断用途</Tag>
          </Space>
        </Form>
      </Modal>

      <Drawer title='影像输入详情' width={560} open={!!detail} onClose={() => setDetail(null)}>
        {detail ? (
          <Descriptions column={1} size='small' bordered>
            <Descriptions.Item label='影像输入 ID'>{detail.input_asset_id}</Descriptions.Item>
            <Descriptions.Item label='系统溯源编号'>{detail.trace_id || '-'}</Descriptions.Item>
            <Descriptions.Item label='来源类型'>{sourceLabel(detail.source_type)}</Descriptions.Item>
            <Descriptions.Item label='DICOM / 存储引用'>{detail.storage_uri}</Descriptions.Item>
            <Descriptions.Item label='预处理状态'>{workflowStatusLabel(detail, statuses[detail.input_asset_id])}</Descriptions.Item>
            <Descriptions.Item label='上传状态'>{String((statuses[detail.input_asset_id]?.provenance_json as Record<string, unknown> | undefined)?.upload_state || (detail.provenance_json as Record<string, unknown> | undefined)?.upload_state || '-')}</Descriptions.Item>
            <Descriptions.Item label='文件数量'>{String((statuses[detail.input_asset_id]?.provenance_json as Record<string, unknown> | undefined)?.upload_file_count || (detail.provenance_json as Record<string, unknown> | undefined)?.upload_file_count || '-')}</Descriptions.Item>
            <Descriptions.Item label='文件摘要'>{uploadManifestSummary(statuses[detail.input_asset_id])}</Descriptions.Item>
            <Descriptions.Item label='脱敏'>{detail.deidentified ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label='非诊断'>{detail.not_for_diagnosis ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label='转换工具'>{statuses[detail.input_asset_id]?.conversion_tool || '-'}</Descriptions.Item>
            <Descriptions.Item label='原始输出文件'>{statuses[detail.input_asset_id]?.raw_output_file || '-'}</Descriptions.Item>
            <Descriptions.Item label='偏置场校正'>{statuses[detail.input_asset_id]?.bias_correction || '-'}</Descriptions.Item>
            <Descriptions.Item label='模型输入文件'>{statuses[detail.input_asset_id]?.model_input_file || '-'}</Descriptions.Item>
            <Descriptions.Item label='提示信息'>{statuses[detail.input_asset_id]?.message || '-'}</Descriptions.Item>
          </Descriptions>
        ) : null}
      </Drawer>
    </Space>
  );
}
