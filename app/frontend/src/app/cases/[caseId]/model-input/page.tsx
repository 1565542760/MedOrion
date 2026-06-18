'use client';

import { use, useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Drawer, Input, InputNumber, Select, Space, Table, Tag, Typography } from 'antd';
import { CaseSubNav } from '@/components/CaseSubNav';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
import {
  formatApiErrorMessage,
  createClinicalTableSnapshotFromValidation,
  getModelInputSnapshot,
  listCases,
  listModelInputSnapshotsByCase,
  listPatients,
  validateClinicalTableInput,
  type CaseItem,
  type ClinicalTableStrictFeatureMappingItemV1,
  type ClinicalTableStrictValidationResponseV1,
  type PatientItem,
} from '@/lib/api';

type Params = { caseId: string };
type FieldType = 'number' | 'binary' | 'coded_sputum';
type FieldDefinition = { order: number; model: string; label: string; type: FieldType; coding: string; note: string };
type DraftValues = Record<string, number | string | null | undefined>;
type CsvPreviewRow = { key: string; rawColumn: string; targetFeature: string | null; rawValue: string; parsedValue: number | string | null; status: 'matched' | 'unmatched' | 'empty' };

function normalizeSnapshotValue(feature: string, value: unknown) {
  const field = FIELD_BY_MODEL.get(feature);
  if (!field) return value;
  if (field.type === 'binary') {
    if (value === true) return 1;
    if (value === false) return 0;
  }
  if (field.type === 'coded_sputum' && typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : value;
  }
  return value;
}

function snapshotToValues(snapshot: { mapped_features?: Record<string, unknown> | null }) {
  const next: DraftValues = {};
  const mapped = snapshot.mapped_features || {};
  for (const [feature, value] of Object.entries(mapped)) {
    next[feature] = normalizeSnapshotValue(feature, value) as DraftValues[string];
  }
  return next;
}

const SPUTUM_FIELD = 'Sputum production (0 none; 1 white; 2 yellow; 3 bloody; 4 not specified; 5 rust-colored; 6 green)';

const FIELDS: FieldDefinition[] = [
  { order: 1, model: 'Age', label: '年龄', type: 'number', coding: '数值', note: '患者年龄' },
  { order: 2, model: 'Height', label: '身高', type: 'number', coding: '数值', note: '单位按训练表格保持一致' },
  { order: 3, model: 'Weight', label: '体重', type: 'number', coding: '数值', note: '单位按训练表格保持一致' },
  { order: 4, model: 'BMI', label: 'BMI', type: 'number', coding: '数值', note: '体重指数' },
  { order: 5, model: 'Hospitalization_duration', label: '住院时长', type: 'number', coding: '数值', note: '剔除入院/出院日期后保留的时长字段' },
  { order: 6, model: 'Upper_left_lung', label: '左上肺', type: 'binary', coding: '0 否 / 1 是', note: '病灶部位' },
  { order: 7, model: 'Lower_left_lung', label: '左下肺', type: 'binary', coding: '0 否 / 1 是', note: '病灶部位' },
  { order: 8, model: 'Right_upper_lung', label: '右上肺', type: 'binary', coding: '0 否 / 1 是', note: '病灶部位' },
  { order: 9, model: 'Right_middle_lung', label: '右中肺', type: 'binary', coding: '0 否 / 1 是', note: '病灶部位' },
  { order: 10, model: 'Right_lower_lung', label: '右下肺', type: 'binary', coding: '0 否 / 1 是', note: '病灶部位' },
  { order: 11, model: 'Whole_lung_lesion', label: '全肺病变', type: 'binary', coding: '0 否 / 1 是', note: '病灶范围' },
  { order: 12, model: 'The_lesion_is_located_subpleurally', label: '胸膜下病变', type: 'binary', coding: '0 否 / 1 是', note: '病灶是否位于胸膜下' },
  { order: 13, model: 'dizziness', label: '晕征', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 14, model: 'Anti-dizziness_signs', label: '反晕征', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 15, model: 'Tree_Bud_Syndrome', label: '树芽征', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 16, model: 'Striated_shadow', label: '条索状影', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 17, model: 'Frosted_Glass_Shadow', label: '磨玻璃影', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 18, model: 'Bronchial_inflation_sign', label: '支气管充气征', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 19, model: 'Hilar_lymphadenopathy', label: '肺门淋巴结肿大', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 20, model: 'Pleural_traction', label: '胸膜牵拉', type: 'binary', coding: '0 否 / 1 是', note: '影像征象' },
  { order: 21, model: 'Fever', label: '发热', type: 'binary', coding: '0 否 / 1 是', note: '临床症状' },
  { order: 22, model: 'Cough', label: '咳嗽', type: 'binary', coding: '0 否 / 1 是', note: '二值字段，不是咳痰编码' },
  { order: 23, model: SPUTUM_FIELD, label: '咳痰', type: 'coded_sputum', coding: '0 无痰 / 1 白痰 / 2 黄痰 / 3 血痰 / 4 未说明 / 5 铁锈色痰 / 6 绿色痰', note: '独立于咳嗽字段' },
  { order: 24, model: 'chest_tightness', label: '胸闷', type: 'binary', coding: '0 否 / 1 是', note: '临床症状' },
  { order: 25, model: 'Shortness_of_breath', label: '气短', type: 'binary', coding: '0 否 / 1 是', note: '临床症状' },
  { order: 26, model: 'Coughing_up_blood', label: '咯血', type: 'binary', coding: '0 否 / 1 是', note: '临床症状' },
  { order: 27, model: 'Weight_loss', label: '体重下降', type: 'binary', coding: '0 否 / 1 是', note: '临床症状' },
  { order: 28, model: 'Lymphocyte_count', label: '淋巴细胞计数', type: 'number', coding: '数值', note: '实验室指标' },
  { order: 29, model: 'ESR', label: '血沉', type: 'number', coding: '数值', note: '实验室指标' },
  { order: 30, model: 'C-reactive_protein', label: 'C反应蛋白', type: 'number', coding: '数值', note: '实验室指标' },
  { order: 31, model: 'High-sensitivity_C-reactive_protein', label: '超敏C反应蛋白', type: 'number', coding: '数值', note: '实验室指标' },
  { order: 32, model: 'Procalcitonin', label: '降钙素原', type: 'number', coding: '数值', note: '实验室指标' },
  { order: 33, model: 'CEA', label: 'CEA', type: 'number', coding: '数值', note: '肿瘤标志物' },
  { order: 34, model: 'CA153', label: 'CA153', type: 'number', coding: '数值', note: '肿瘤标志物' },
  { order: 35, model: 'Serum_non-small_cell lung_cancer-related antigen', label: '血清非小细胞肺癌相关抗原', type: 'number', coding: '数值', note: '肿瘤标志物' },
  { order: 36, model: 'Striated_shadow.1', label: '网格状影', type: 'binary', coding: '0 否 / 1 是', note: '训练表格保留字段，不能与条索状影互换' },
];

const FIELD_BY_MODEL = new Map(FIELDS.map((field) => [field.model, field]));
const FIELD_BY_LABEL = new Map(FIELDS.map((field) => [field.label, field]));

function statusColor(value?: string | null) { if (value === 'ready_for_inference') return 'green'; if (value === 'insufficient_data_for_assessment') return 'red'; if (value === 'schema_unverified') return 'orange'; return 'default'; }
function statusText(value?: string | null) { if (value === 'ready_for_inference') return '可创建快照'; if (value === 'insufficient_data_for_assessment') return '必填字段缺失'; if (value === 'schema_unverified') return '字段需修正'; return '待校验'; }

function parseCsvLine(line: string) { const result: string[] = []; let current = ''; let quoted = false; for (let i = 0; i < line.length; i += 1) { const char = line[i]; if (char === '"') quoted = !quoted; else if (char === ',' && !quoted) { result.push(current.trim()); current = ''; } else current += char; } result.push(current.trim()); return result; }
function parseNumberLike(value: string) { const trimmed = value.trim(); if (!trimmed || trimmed === '无' || trimmed === '未知' || trimmed === '-') return null; const normalized = trimmed.replace('？', '').replace('?', ''); const num = Number(normalized); return Number.isFinite(num) ? num : trimmed; }
function valueForBackend(values: DraftValues) { const row: Record<string, unknown> = {}; for (const field of FIELDS) { const value = values[field.model]; if (value !== undefined && value !== null && value !== '') row[field.model] = value; } return row; }
function buildPayload(values: DraftValues, sourceType: 'manual_entry' | 'csv_paste') { const sampleRow = valueForBackend(values); return { raw_columns: FIELDS.map((field) => field.model), rows: [sampleRow], sample_row: sampleRow, source_type: sourceType, not_for_diagnosis: true, shadow_only: true }; }
function fieldValidation(feature: string, result: ClinicalTableStrictValidationResponseV1 | null): ClinicalTableStrictFeatureMappingItemV1 | null { return result?.feature_mappings.find((item) => item.model_feature_name === feature) || null; }
function matchColumn(column: string) { return FIELD_BY_MODEL.get(column) || FIELD_BY_LABEL.get(column) || null; }

export default function ModelInputPage({ params }: { params: Promise<Params> }) {
  const { caseId } = use(params);
  const [caseRecord, setCaseRecord] = useState<CaseItem | null>(null);
  const [patient, setPatient] = useState<PatientItem | null>(null);
  const [values, setValues] = useState<DraftValues>({});
  const [validation, setValidation] = useState<ClinicalTableStrictValidationResponseV1 | null>(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [creating, setCreating] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [csvText, setCsvText] = useState('');
  const [csvPreview, setCsvPreview] = useState<CsvPreviewRow[]>([]);
  const draftKey = 'medorion:capcop:clinical-draft:' + caseId;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [cases, patients, snapshotList] = await Promise.all([listCases(), listPatients(), listModelInputSnapshotsByCase(caseId, undefined, 1, 0)]);
      const foundCase = cases.find((item) => item.case_id === caseId) || null;
      setCaseRecord(foundCase);
      setPatient(patients.find((item) => item.patient_id === foundCase?.patient_id) || null);
      const latestSnapshotId = snapshotList.items?.[0]?.input_snapshot_id || null;
      if (latestSnapshotId) {
        try {
          const latestSnapshot = await getModelInputSnapshot(latestSnapshotId);
          const nextValues = snapshotToValues(latestSnapshot);
          setValues(nextValues);
          try {
            const refreshed = await validateClinicalTableInput(caseId, buildPayload(nextValues, 'manual_entry'));
            setValidation(refreshed);
            setMessage('已加载最新临床输入快照，系统已完成自动校验。');
          } catch {
            setValidation(null);
            setMessage('已加载最新临床输入快照，但自动校验未通过，请检查字段。');
          }
        } catch {
          const rawDraft = window.localStorage.getItem(draftKey);
          if (rawDraft) setValues(JSON.parse(rawDraft) as DraftValues);
        }
      } else {
        const rawDraft = window.localStorage.getItem(draftKey);
        if (rawDraft) setValues(JSON.parse(rawDraft) as DraftValues);
      }
    } finally {
      setLoading(false);
    }
  }, [caseId, draftKey]);
  useEffect(() => { const timer = window.setTimeout(() => { void load(); }, 0); return () => window.clearTimeout(timer); }, [load]);

  const updateValue = (field: FieldDefinition, value: number | string | null) => { setValues((prev) => ({ ...prev, [field.model]: value })); setValidation(null); };
  const saveDraft = () => { window.localStorage.setItem(draftKey, JSON.stringify(values)); setMessage('草稿已保存到本机浏览器，不写入数据库。'); };
  const validate = async () => { setValidating(true); setMessage(''); try { const result = await validateClinicalTableInput(caseId, buildPayload(values, 'manual_entry')); setValidation(result); setMessage(result.can_create_snapshot ? '字段校验通过，可以创建输入快照。' : '字段校验未通过，请根据表格状态修正。'); } catch (error) { setMessage(formatApiErrorMessage(error, '字段校验失败，请稍后重试。')); } finally { setValidating(false); } };
  const createSnapshot = async () => { setCreating(true); setMessage(''); try { const result = await createClinicalTableSnapshotFromValidation(caseId, { ...buildPayload(values, 'manual_entry'), trace_id: caseRecord?.trace_id || null }); const nextMessage = result.snapshot_created ? '输入快照已创建，可进入模型评估。' : '未创建输入快照：' + (result.failure_reasons || []).join('、'); await load(); setMessage(nextMessage); } catch (error) { setMessage(formatApiErrorMessage(error, '创建输入快照失败，请稍后重试。')); } finally { setCreating(false); } };
  const previewCsv = () => { const lines = csvText.split(/\r?\n/).map((line) => line.trim()).filter(Boolean); if (lines.length < 2) { setCsvPreview([]); return; } const columns = parseCsvLine(lines[0]); const firstRow = parseCsvLine(lines[1]); setCsvPreview(columns.map((column, index) => { const match = matchColumn(column); const rawValue = firstRow[index] || ''; return { key: column + index, rawColumn: column, targetFeature: match?.model || null, rawValue, parsedValue: rawValue ? parseNumberLike(rawValue) : null, status: match ? (rawValue ? 'matched' : 'empty') : 'unmatched' }; })); };
  const applyCsv = () => { const next = { ...values }; for (const row of csvPreview) { if (row.targetFeature && row.parsedValue !== null && row.parsedValue !== '') next[row.targetFeature] = row.parsedValue; } setValues(next); setValidation(null); setDrawerOpen(false); setMessage('CSV 第一行样例已应用到表格，请重新字段校验。'); };
  const rows = useMemo(() => FIELDS.map((field) => { const check = fieldValidation(field.model, validation); const hasValue = values[field.model] !== undefined && values[field.model] !== null && values[field.model] !== ''; return { ...field, value: values[field.model], check, hasValue }; }), [validation, values]);

  const columns = [
    { title: '序号', dataIndex: 'order', width: 72, fixed: 'left' as const },
    { title: '中文字段', dataIndex: 'label', width: 240, fixed: 'left' as const, render: (value: string, row: FieldDefinition) => <Space direction='vertical' size={0}><Space size={8}><Typography.Text strong>{value}</Typography.Text>{row.model === 'Striated_shadow.1' ? <Tag color='orange'>保留字段</Tag> : null}</Space><Typography.Text type='secondary' style={{ fontSize: 12 }} copyable>{row.model}</Typography.Text></Space> },
    { title: '值', width: 260, render: (_: unknown, row: FieldDefinition & { value?: number | string | null }) => { if (row.type === 'binary') return <Select allowClear placeholder='请选择' value={row.value as number | undefined} style={{ width: 170 }} onChange={(value) => updateValue(row, value ?? null)} options={[{ label: '是', value: 1 }, { label: '否', value: 0 }]} />; if (row.type === 'coded_sputum') return <Select allowClear placeholder='请选择' value={row.value as number | undefined} style={{ width: 220 }} onChange={(value) => updateValue(row, value ?? null)} options={[{ label: '0 无痰', value: 0 }, { label: '1 白痰', value: 1 }, { label: '2 黄痰', value: 2 }, { label: '3 血痰', value: 3 }, { label: '4 未说明', value: 4 }, { label: '5 铁锈色痰', value: 5 }, { label: '6 绿色痰', value: 6 }]} />; return <InputNumber placeholder='输入数值' value={typeof row.value === 'number' ? row.value : null} style={{ width: 170 }} onChange={(value) => updateValue(row, value)} />; } },
    { title: '状态', width: 180, render: (_: unknown, row: FieldDefinition & { check: ClinicalTableStrictFeatureMappingItemV1 | null; hasValue: boolean }) => row.check ? <Tag color={row.check.coercion_status === 'ok' ? 'green' : row.check.coercion_status === 'missing' ? 'red' : 'orange'}>{row.check.message || row.check.coercion_status}</Tag> : <Tag color={row.hasValue ? 'blue' : 'default'}>{row.hasValue ? '已填写' : '待填写'}</Tag> },
  ];

  return (
    <main style={{ padding: 24, width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <CaseSubNav caseId={caseId} patientName={patient?.display_name || undefined} patientId={patient?.external_patient_id || patient?.patient_id} caseNo={caseRecord?.case_no} />
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <Space direction='vertical' size={4}><Typography.Title level={3} style={{ margin: 0 }}>临床输入</Typography.Title><Typography.Text type='secondary'>按训练 artifact 的 36 字段顺序录入，先校验再建快照。</Typography.Text></Space>
          <Space wrap><Tag color={statusColor(validation?.validation_status)}>{statusText(validation?.validation_status)}</Tag><Tag color='gold'>院内录入，结果仅用于模型评估</Tag></Space>
        </div>
        {message ? <Alert type={validation?.can_create_snapshot ? 'success' : 'info'} showIcon message={message} /> : null}
        <WorkspaceTableShell title='CAP/COP 临床表格字段' subtitle='一页只保留这一张主表，滚动都在窗口内。' actions={<Space wrap><Button onClick={() => setDrawerOpen(true)}>CSV 导入</Button><Button onClick={saveDraft}>保存草稿</Button><Button loading={validating} type='primary' onClick={validate}>字段校验</Button><Button loading={creating} disabled={!validation?.can_create_snapshot} onClick={createSnapshot}>创建输入快照</Button></Space>} minHeight={560}>
          <Table rowKey='model' size='small' loading={loading} columns={columns} dataSource={rows} pagination={false} sticky scroll={{ x: 980, y: 'calc(100vh - 330px)' }} />
        </WorkspaceTableShell>
      </Space>
      <Drawer title='CSV 导入预览' width={760} open={drawerOpen} onClose={() => setDrawerOpen(false)} extra={<Space><Button onClick={previewCsv}>解析预览</Button><Button type='primary' disabled={csvPreview.length === 0} onClick={applyCsv}>应用到表格</Button></Space>}>
        <Space direction='vertical' size={16} style={{ width: '100%' }}>
          <Alert type='info' showIcon message='CSV 只用于字段映射和值解析预览，不会直接创建输入快照。' />
          <Input.TextArea rows={8} value={csvText} onChange={(event) => setCsvText(event.target.value)} placeholder={'粘贴表头和第一行样例，例如：\nAge,Height,Weight,Cough,' + SPUTUM_FIELD + '\n68,170,65,1,2'} />
          <Table rowKey='key' size='small' pagination={false} columns={[{ title: '原始列名', dataIndex: 'rawColumn', width: 180, fixed: 'left' as const }, { title: '匹配字段', dataIndex: 'targetFeature', width: 260, render: (value: string | null) => value ? <Typography.Text type='secondary'>{FIELD_BY_MODEL.get(value)?.label} / {value}</Typography.Text> : <Tag color='red'>未匹配</Tag> }, { title: '原始值', dataIndex: 'rawValue', width: 140 }, { title: '解析后值', dataIndex: 'parsedValue', width: 140, render: (value: unknown) => value === null || value === undefined ? '-' : String(value) }, { title: '状态', dataIndex: 'status', width: 120, render: (value: CsvPreviewRow['status']) => <Tag color={value === 'matched' ? 'green' : value === 'empty' ? 'orange' : 'red'}>{value === 'matched' ? '可应用' : value === 'empty' ? '空值' : '未匹配'}</Tag> }]} dataSource={csvPreview} sticky scroll={{ x: 900, y: 360 }} />
        </Space>
      </Drawer>
    </main>
  );
}
