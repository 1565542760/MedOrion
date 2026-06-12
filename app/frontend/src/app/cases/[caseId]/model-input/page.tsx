
'use client';

import Link from 'next/link';
import axios from 'axios';
import { use, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Col, Descriptions, Input, InputNumber, Row, Select, Space, Spin, Table, Tag, Typography } from 'antd';
import {
  createModelInputSnapshot,
  getModel,
  getModelFeatureRequirements,
  getModelInputSchema,
  getShadowRunOutputs,
  listModelInputSnapshotsByCase,
  listCases,
  listModels,
  previewCaseModelInput,
  previewModelSelection,
  runClinicalMlpFold5OneShotShadow,
  validateCaseModelInput,
  type ModelInputFeatureRequirement,
  type ModelInputPreviewItem,
  type ModelInputPreviewPayload,
  type ModelInputSchemaResponse,
  type ModelSelectionCandidate,
  type ModelSelectionPreviewResponse,
  type ControlledShadowClinicalMlpFold5OneShotResponse,
  type ModelInputSnapshotCreatePayload,
  type ModelInputSnapshotSummaryItem,
  type ModelVersionItem,
} from '@/lib/api';

type CaseRecord = {
  case_id: string;
  case_no?: string | null;
  disease_task?: string | null;
  status?: string | null;
  trace_id?: string | null;
  patient_id?: string | null;
  chief_complaint?: string | null;
};

type ModelVersionOption = ModelVersionItem & {
  model_name: string;
  disease_agent: string;
  task_type: string;
  modality_scope: string[];
  owner_team: string;
  description?: string | null;
  is_active: boolean;
  model_input_schema_id?: string | null;
  model_input_schema_key?: string | null;
  lifecycle_status?: string | null;
  supported_modalities?: string[];
};

function extractErrorCode(error: unknown) {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as {
      detail?: { code?: string; message?: string } | string;
      code?: string;
      message?: string;
    } | undefined;

    if (typeof data?.detail === 'string') return data.detail;
    if (data?.detail && typeof data.detail === 'object' && data.detail.code) return data.detail.code;
    if (data?.code) return data.code;
    if (data?.message) return data.message;
    if (error.response?.status === 404) return 'not_found';
    if (error.response?.status === 422) return 'validation_error';
  }

  if (error instanceof Error) return error.message;
  return 'unknown_error';
}

function translateError(error: unknown) {
  const code = extractErrorCode(error);
  switch (code) {
    case 'case_not_found':
      return '病例不存在';
    case 'model_input_schema_not_found':
      return '模型输入 schema 未找到';
    case 'unsupported_disease_task':
      return '当前病種任务暂不支持该模型输入预览';
    case 'insufficient_data_for_assessment':
      return '模型输入 schema 未找到';
    case 'missing_required_features':
      return '缺少必需特征，不能 silent fallback';
    case 'validation_error':
      return '请求参数校验未通过';
    case 'not_found':
      return '请求的资源不存在';
    default:
      return code && code !== 'unknown_error' ? '请求失败：' + code : '请求失败，请稍后重试';
  }
}

function renderTags(values: string[] | undefined, color: string = 'default') {
  if (!values || values.length === 0) return '-';
  return (
    <Space wrap size={[6, 6]}>
      {values.map((value) => (
        <Tag key={value} color={color}>{value}</Tag>
      ))}
    </Space>
  );
}

function renderFeatureBool(value?: boolean | null) {
  return value ? <Tag color='green'>是</Tag> : <Tag>否</Tag>;
}

function getProvidedFeatures(item: ModelInputPreviewItem | null) {
  if (!item) return [] as string[];
  if (Array.isArray(item.provided_features)) return item.provided_features.map((x) => String(x));
  if (item.mapped_features && typeof item.mapped_features === 'object') return Object.keys(item.mapped_features);
  return [] as string[];
}

function getMissingRequiredQuestions(item: ModelInputPreviewItem | null) {
  if (!item) return [] as string[];
  const fromDetails = (item.missing_required_details || [])
    .map((detail) => detail.suggested_doctor_question)
    .filter((value): value is string => !!value);
  if (fromDetails.length > 0) return fromDetails;
  return item.suggested_doctor_questions || [];
}

type SnapshotValue = number | string | null;

function normalizeContractToken(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '');
}

function splitCsvLine(value: string) {
  return value
    .split(',')
    .map((item) => item.trim().replace(/^\"|\"$/g, ''))
    .filter((item, index, array) => !(index === array.length - 1 && item === ''));
}

function parseCsvPreview(text: string) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const headers = lines[0] ? splitCsvLine(lines[0]) : [];
  const sampleRow = lines[1] ? splitCsvLine(lines[1]) : [];
  return { headers, sampleRow };
}

const FEATURE_LABEL_MAP: Record<string, string> = {
  Age: '年龄',
  Sex: '性别',
  Temperature: '体温',
  HeartRate: '心率',
  RespiratoryRate: '呼吸频率',
  SPO2: '血氧饱和度',
  SystolicBP: '收缩压',
  DiastolicBP: '舒张压',
  WBC: '白细胞',
  NeutrophilPercent: '中性粒细胞百分比',
  LymphocytePercent: '淋巴细胞百分比',
  CRP: 'C 反应蛋白',
  Procalcitonin: '降钙素原',
  ESR: '血沉',
  Hemoglobin: '血红蛋白',
  Platelet: '血小板',
  Sodium: '钠',
  Potassium: '钾',
  Chloride: '氯',
  BUN: '尿素氮',
  Creatinine: '肌酐',
  ALT: '丙氨酸转氨酶',
  AST: '天门冬氨酸转氨酶',
  Albumin: '白蛋白',
  Glucose: '血糖',
  Cough: '咳嗽',
  Fever: '发热',
  Dyspnea: '呼吸困难',
  ChestPain: '胸痛',
  Wheeze: '喘鸣',
  Crackles: '湿啰音',
  Consolidation: '实变',
  PleuralEffusion: '胸腔积液',
  Infiltration: '浸润',
  'Striated_shadow.1': '条索影.1 / 历史 schema 保留字段',
  SmokingHistory: '吸烟史',
};

function getFeatureDisplayName(item: ModelInputFeatureRequirement) {
  return FEATURE_LABEL_MAP[item.model_feature_name] || item.source_clinical_field || item.model_feature_name;
}

const RAW_FIELD_LABEL_MAP: Record<string, string> = {
  Classification: '分型标签',
  Desensitized_ID: '脱敏病例 ID',
  Age: '年龄',
  Height: '身高',
  Weight: '体重',
  BMI: 'BMI',
  Hospitalization_duration: '住院时长',
  Upper_left_lung: '左上肺',
  Lower_left_lung: '左下肺',
  Right_upper_lung: '右上肺',
  Right_middle_lung: '右中肺',
  Right_lower_lung: '右下肺',
  Whole_lung_lesion: '全肺病灶',
  The_lesion_is_located_subpleurally: '病灶贴胸膜',
  dizziness: '头晕',
  'Anti-dizziness_signs': '头晕伴随体征',
  Tree_Bud_Syndrome: '树芽征',
  Striated_shadow: '条索影',
  Frosted_Glass_Shadow: '磨玻璃影',
  Bronchial_inflation_sign: '支气管充气征',
  Hilar_lymphadenopathy: '肺门淋巴结肿大',
  Pleural_traction: '胸膜牵拉',
  Fever: '发热',
  Cough: '咳嗽',
  'Sputum production (0 none; 1 white; 2 yellow; 3 bloody; 4 not specified; 5 rust-colored; 6 green)': '痰液性质',
  chest_tightness: '胸闷',
  Shortness_of_breath: '呼吸困难',
  Coughing_up_blood: '咯血',
  Weight_loss: '体重下降',
  Lymphocyte_count: '淋巴细胞计数',
  ESR: '血沉',
  'C-reactive_protein': 'C 反应蛋白',
  'High-sensitivity_C-reactive_protein': '高敏 C 反应蛋白',
  Procalcitonin: '降钙素原',
  CEA: '癌胚抗原',
  CA153: 'CA15-3',
  'Serum_non-small_cell lung_cancer-related antigen': '血清非小细胞肺癌相关抗原',
};

function getSourceFieldDisplayName(item: ModelInputFeatureRequirement) {
  return RAW_FIELD_LABEL_MAP[item.source_clinical_field] || item.source_clinical_field || '-';
}

type FieldSourceStatus = 'preprocess_artifact_confirmed' | 'product_schema_only' | 'csv_synonym' | 'unverified';

function getFieldSourceStatus(item: ModelInputFeatureRequirement): FieldSourceStatus {
  if (item.model_feature_name === 'Sex') return 'unverified';
  if (item.model_feature_name === 'Striated_shadow.1') return 'product_schema_only';
  if (item.model_feature_name === 'Dyspnea' || item.model_feature_name === 'CRP' || item.model_feature_name === 'Procalcitonin') {
    return 'csv_synonym';
  }
  return 'product_schema_only';
}

function getFieldSourceStatusLabel(status: FieldSourceStatus) {
  switch (status) {
    case 'preprocess_artifact_confirmed':
      return 'preprocess_artifact_confirmed';
    case 'product_schema_only':
      return 'product_schema_only';
    case 'csv_synonym':
      return 'csv_synonym';
    case 'unverified':
      return 'unverified';
    default:
      return status;
  }
}

function getFieldSourceStatusColor(status: FieldSourceStatus) {
  switch (status) {
    case 'preprocess_artifact_confirmed':
      return 'green';
    case 'csv_synonym':
      return 'blue';
    case 'product_schema_only':
      return 'gold';
    case 'unverified':
      return 'orange';
    default:
      return 'default';
  }
}

function getFeatureTypeLabel(item: ModelInputFeatureRequirement) {
  if (item.model_feature_name === 'Striated_shadow.1') return '历史保留字段';
  switch (item.feature_type) {
    case 'numeric':
      return '数值';
    case 'boolean':
      return '二值';
    case 'categorical':
      return '分类';
    default:
      return '待确认';
  }
}

function isEmptySnapshotValue(value: SnapshotValue) {
  return value === null || value === undefined || Number.isNaN(value);
}

function buildSyntheticBaseline(requirements: ModelInputFeatureRequirement[]) {
  const baseline: Record<string, SnapshotValue> = {};
  requirements.forEach((item, index) => {
    if (item.model_feature_name === 'Sex') {
      baseline[item.model_feature_name] = 'male';
      return;
    }
    if (item.model_feature_name === 'Dyspnea') {
      baseline[item.model_feature_name] = 'mild';
      return;
    }
    if (item.model_feature_name === 'SmokingHistory') {
      baseline[item.model_feature_name] = 'never';
      return;
    }
    if (item.feature_type === 'boolean') {
      baseline[item.model_feature_name] = 1;
      return;
    }
    const seed = Number((index + 1 + (item.required ? 0.1 : 0.6)).toFixed(1));
    baseline[item.model_feature_name] = seed;
  });
  return baseline;
}

function statusLabel(value?: string | null) {
  if (!value) return '-';
  switch (value) {
    case 'ready_for_inference':
      return '可用于 Shadow 评估';
    case 'insufficient_data_for_assessment':
      return '当前数据不足以判断';
    case 'missing_required_features':
      return '缺少必需特征';
    case 'default_applied':
      return '已应用默认策略';
    case 'doctor_confirmation_required':
      return '需要医生确认';
    case 'validation_failed':
      return '校验失败';
    default:
      return value;
  }
}

function getBooleanOptions(item: ModelInputFeatureRequirement) {
  if (item.model_feature_name === 'Striated_shadow.1') {
    return [
      { label: '存在', value: '1' },
      { label: '不存在', value: '0' },
      { label: '未知', value: 'unknown' },
    ];
  }
  return [
    { label: '是', value: '1' },
    { label: '否', value: '0' },
    { label: '未知', value: 'unknown' },
  ];
}

function getCategoricalOptions(item: ModelInputFeatureRequirement) {
  const allowed = item.value_range && typeof item.value_range === 'object' && Array.isArray((item.value_range as { allowed?: unknown[] }).allowed)
    ? ((item.value_range as { allowed: unknown[] }).allowed as Array<string | number>)
    : [];
  if (item.model_feature_name === 'Sex') {
    return [
      { label: '男', value: 'male' },
      { label: '女', value: 'female' },
      { label: '未知', value: 'unknown' },
    ];
  }
  if (item.model_feature_name === 'Dyspnea') {
    return [
      { label: '无', value: 'none' },
      { label: '轻度', value: 'mild' },
      { label: '中度', value: 'moderate' },
      { label: '重度', value: 'severe' },
      { label: '未知', value: 'unknown' },
    ];
  }
  if (item.model_feature_name === 'SmokingHistory') {
    return [
      { label: '从不', value: 'never' },
      { label: '既往', value: 'former' },
      { label: '当前', value: 'current' },
      { label: '未知', value: 'unknown' },
    ];
  }
  return allowed.map((value) => ({ label: String(value), value: String(value) }));
}

function renderFeatureInput(item: ModelInputFeatureRequirement, value: SnapshotValue, onChange: (next: SnapshotValue) => void) {
  if (item.feature_type === 'categorical') {
    return (
      <Select
        style={{ width: '100%' }}
        value={value === null || value === undefined ? undefined : String(value)}
        onChange={(next) => onChange(String(next))}
        options={getCategoricalOptions(item)}
        placeholder='请选择'
        allowClear
      />
    );
  }
  if (item.feature_type === 'boolean') {
    const nextValue = value === 1 ? '1' : value === 0 ? '0' : value === 'unknown' ? 'unknown' : undefined;
    return (
      <Select
        style={{ width: '100%' }}
        value={nextValue}
        onChange={(next) => onChange(next === '1' ? 1 : next === '0' ? 0 : null)}
        options={getBooleanOptions(item)}
        placeholder='请选择'
        allowClear
      />
    );
  }
  return (
    <InputNumber
      value={typeof value === 'number' ? value : null}
      onChange={(next) => onChange(typeof next === 'number' ? next : null)}
      style={{ width: '100%' }}
      placeholder='请输入数值'
    />
  );
}

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [queryModelVersionId] = useState(() => {
    if (typeof window === 'undefined') return '';
    return new URLSearchParams(window.location.search).get('model_version_id') || '';
  });
  const [selectedVersionId, setSelectedVersionId] = useState('');
  const [loadingPage, setLoadingPage] = useState(true);
  const [selectionLoading, setSelectionLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [pageError, setPageError] = useState('');
  const [selectionError, setSelectionError] = useState('');
  const [previewError, setPreviewError] = useState('');
  const [caseRecord, setCaseRecord] = useState<CaseRecord | null>(null);
  const [versionOptions, setVersionOptions] = useState<ModelVersionOption[]>([]);
  const [schema, setSchema] = useState<ModelInputSchemaResponse | null>(null);
  const [requirements, setRequirements] = useState<ModelInputFeatureRequirement[]>([]);
  const [selectionPreview, setSelectionPreview] = useState<ModelSelectionPreviewResponse | null>(null);
  const [previewResult, setPreviewResult] = useState<ModelInputPreviewItem | null>(null);
  const [validationResult, setValidationResult] = useState<ModelInputPreviewItem | null>(null);
  const [snapshotValues, setSnapshotValues] = useState<Record<string, SnapshotValue>>({});
  const [snapshotTraceId, setSnapshotTraceId] = useState('');
  const [snapshotValidationOnly, setSnapshotValidationOnly] = useState(false);
  const [snapshotSubmitting, setSnapshotSubmitting] = useState(false);
  const [snapshotNotice, setSnapshotNotice] = useState('');
  const [snapshotNoticeType, setSnapshotNoticeType] = useState<'success' | 'info' | 'warning' | 'error'>('info');
  const [artifactCsvText, setArtifactCsvText] = useState('');
  const [artifactCsvPreviewReady, setArtifactCsvPreviewReady] = useState(false);
  const [snapshotRows, setSnapshotRows] = useState<ModelInputSnapshotSummaryItem[]>([]);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [shadowRunningSnapshotId, setShadowRunningSnapshotId] = useState('');
  const [shadowRunNotice, setShadowRunNotice] = useState('');
  const [shadowRunNoticeType, setShadowRunNoticeType] = useState<'success' | 'info' | 'warning' | 'error'>('info');
  const [shadowRunResult, setShadowRunResult] = useState<ControlledShadowClinicalMlpFold5OneShotResponse | null>(null);
  const [shadowRunOutputId, setShadowRunOutputId] = useState('');


  useEffect(() => {
    let active = true;

    async function loadPage() {
      setLoadingPage(true);
      setPageError('');

      try {
        const [cases, registry] = await Promise.all([listCases(), listModels()]);
        const currentCase = (cases as CaseRecord[]).find((item) => item.case_id === caseId) || null;
        if (!currentCase) {
          throw new Error('case_not_found');
        }

        const registryDetails = await Promise.all(
          registry.items
            .filter((item) => item.disease_agent === 'capcop_agent' || item.task_type === 'risk_assessment')
            .map(async (item) => getModel(item.model_id))
        );

        const options = registryDetails.flatMap((model) =>
          (model.versions || []).map((version) => ({
            ...(version as ModelVersionOption),
            model_name: model.model_name,
            disease_agent: model.disease_agent,
            task_type: model.task_type,
            modality_scope: model.modality_scope,
            owner_team: model.owner_team,
            description: model.description,
            is_active: model.is_active,
          }))
        ).filter((item) => item.model_input_schema_id === 'clinical_mlp_cap_cop_input_schema_v1' || item.disease_agent === 'capcop_agent');

        if (options.length === 0) {
          throw new Error('model_input_schema_not_found');
        }

        const preferredVersion = queryModelVersionId
          || options.find((item) => item.model_input_schema_id === 'clinical_mlp_cap_cop_input_schema_v1')?.version_id
          || options[0]?.version_id
          || '';

        setCaseRecord(currentCase);
        setVersionOptions(options);
        setSelectedVersionId(preferredVersion);
      } catch (error) {
        if (!active) return;
        setPageError(translateError(error));
      } finally {
        if (active) setLoadingPage(false);
      }
    }

    loadPage();
    return () => {
      active = false;
    };
  }, [caseId, queryModelVersionId]);

  const selectedVersion = useMemo(
    () => versionOptions.find((item) => item.version_id === selectedVersionId) || null,
    [selectedVersionId, versionOptions],
  );
  const schemaUnverified = true;

  useEffect(() => {
    void (async () => {
      if (caseRecord?.trace_id) {
        setSnapshotTraceId(caseRecord.trace_id);
        return;
      }
      setSnapshotTraceId((current) => current || 'trace_manual_snapshot_' + Date.now());
    })();
  }, [caseRecord?.trace_id]);

  useEffect(() => {
    void (async () => {
      setSnapshotValues({});
      setSnapshotValidationOnly(false);
      setSnapshotNotice('');
    })();
  }, [selectedVersionId]);

  useEffect(() => {
    let active = true;

    async function loadSnapshots() {
      setSnapshotLoading(true);
      try {
        const response = await listModelInputSnapshotsByCase(caseId);
        if (!active) return;
        setSnapshotRows(response.items || []);
      } catch {
        if (!active) return;
        setSnapshotRows([]);
        setSnapshotNoticeType('error');
        setSnapshotNotice('输入快照列表加载失败，请稍后重试。');
      } finally {
        if (active) setSnapshotLoading(false);
      }
    }

    loadSnapshots();
    return () => {
      active = false;
    };
  }, [caseId]);


  useEffect(() => {
    if (!caseRecord?.disease_task || versionOptions.length === 0) return;
    const diseaseTask = caseRecord.disease_task || '';
    let active = true;

    async function loadSelectionPreview() {
      setSelectionLoading(true);
      setSelectionError('');
      try {
        const preview = await previewModelSelection(caseId, {
          disease_task: diseaseTask,
          candidate_model_version_ids: versionOptions.map((item) => item.version_id),
        });
        if (!active) return;
        setSelectionPreview(preview);
      } catch (error) {
        if (!active) return;
        setSelectionPreview(null);
        setSelectionError(translateError(error));
      } finally {
        if (active) setSelectionLoading(false);
      }
    }

    loadSelectionPreview();
    return () => {
      active = false;
    };
  }, [caseId, caseRecord?.disease_task, versionOptions]);

  useEffect(() => {
    if (!caseRecord?.disease_task || !selectedVersionId) return;
    const diseaseTask = caseRecord.disease_task || '';
    let active = true;

    async function loadInputPreview() {
      setPreviewLoading(true);
      setPreviewError('');
      try {
        const payload: ModelInputPreviewPayload = {
          disease_task: diseaseTask,
          model_version_id: selectedVersionId,
        };
        const [schemaData, requirementsData, previewData, validationData] = await Promise.all([
          getModelInputSchema(selectedVersionId),
          getModelFeatureRequirements(selectedVersionId),
          previewCaseModelInput(caseId, payload),
          validateCaseModelInput(caseId, payload),
        ]);
        if (!active) return;
        setSchema(schemaData);
        setRequirements(requirementsData.feature_requirements || schemaData.feature_requirements || []);
        setPreviewResult(previewData);
        setValidationResult(validationData);
      } catch (error) {
        if (!active) return;
        setSchema(null);
        setRequirements([]);
        setPreviewResult(null);
        setValidationResult(null);
        setPreviewError(translateError(error));
      } finally {
        if (active) setPreviewLoading(false);
      }
    }

    loadInputPreview();
    return () => {
      active = false;
    };
  }, [caseId, caseRecord?.disease_task, selectedVersionId]);

  const featureRows = [...requirements].sort((left, right) => left.feature_order - right.feature_order);
  const artifactCsvPreview = useMemo(() => parseCsvPreview(artifactCsvText), [artifactCsvText]);
  const artifactCsvMappingRows = useMemo(() => {
    const headers = artifactCsvPreview.headers;
    const sampleRow = artifactCsvPreview.sampleRow;
    return headers.map((header, index) => {
      const normalizedHeader = normalizeContractToken(header);
      const matchedRequirement = featureRows.find((item) => {
        const featureMatch = normalizeContractToken(item.model_feature_name) === normalizedHeader;
        const sourceMatch = normalizeContractToken(item.source_clinical_field || '') === normalizedHeader;
        const labelMatch = normalizeContractToken(getFeatureDisplayName(item)) === normalizedHeader;
        return featureMatch || sourceMatch || labelMatch;
      }) || null;
      return {
        raw_column: header,
        sample_value: sampleRow[index] || '-',
        artifact_order: matchedRequirement ? matchedRequirement.feature_order : null,
        target_feature: matchedRequirement ? matchedRequirement.model_feature_name : '-',
        source_field: matchedRequirement ? (matchedRequirement.source_clinical_field || '-') : '-',
        status: matchedRequirement ? '����֤' : 'δ��֤ / ��������ģ��',
      };
    });
  }, [artifactCsvPreview.headers, artifactCsvPreview.sampleRow, featureRows]);
  const providedFeatures = getProvidedFeatures(previewResult);
  const missingFeatures = previewResult?.missing_features || validationResult?.missing_features || [];
  const missingRequiredFeatures = previewResult?.missing_required_features || validationResult?.missing_required_features || [];
  const doctorQuestions = getMissingRequiredQuestions(previewResult);
  const defaultableFeatures = previewResult?.defaultable_features || validationResult?.defaultable_features || selectionPreview?.candidates.find((item) => item.model_version_id === selectedVersionId)?.defaultable_features || [];
  const assessmentStatus = previewResult?.current_assessment_status || validationResult?.current_assessment_status || selectionPreview?.candidates.find((item) => item.model_version_id === selectedVersionId)?.current_assessment_status || '-';
  const insufficientData = previewResult?.insufficient_data_for_assessment ?? validationResult?.insufficient_data_for_assessment ?? selectionPreview?.candidates.find((item) => item.model_version_id === selectedVersionId)?.insufficient_data_for_assessment ?? false;
  const selectedCandidate = selectionPreview?.candidates.find((item) => item.model_version_id === selectedVersionId) || null;
  const selectionRequired = selectionPreview?.selection_required ?? versionOptions.length > 1;
  const selectionReason = selectionPreview?.selection_reason || (versionOptions.length > 1 ? 'multiple_candidates' : 'single_candidate');
  const candidateCount = selectionPreview?.candidate_count ?? versionOptions.length;
  const selectionRows: ModelSelectionCandidate[] = selectionPreview?.candidates || versionOptions.map((item) => ({
    model_version_id: item.version_id,
    model_id: item.model_id,
    model_name: item.model_name,
    version_label: item.version_label,
    model_input_schema_id: item.model_input_schema_id || null,
    model_input_schema_key: item.model_input_schema_key || null,
    lifecycle_status: item.lifecycle_status || item.approval_state || null,
    supported_modalities: item.supported_modalities || item.modality_scope,
    feature_completeness: null,
    missing_fields: [],
    missing_required_features: [],
    defaultable_features: [],
    suitability_reason: null,
    current_assessment_status: null,
    insufficient_data_for_assessment: null,
    runtime_stub: null,
  }));

  const snapshotProvidedFeatureNames = Object.entries(snapshotValues)
    .filter(([, value]) => !isEmptySnapshotValue(value))
    .map(([name]) => name);
  const snapshotMappedFeatures = Object.fromEntries(
    Object.entries(snapshotValues).filter(([, value]) => !isEmptySnapshotValue(value)),
  ) as Record<string, unknown>;
  const snapshotMissingFeatures = featureRows
    .filter((item) => isEmptySnapshotValue(snapshotValues[item.model_feature_name]))
    .map((item) => item.model_feature_name);
  const snapshotMissingRequiredFeatures = featureRows
    .filter((item) => item.required && isEmptySnapshotValue(snapshotValues[item.model_feature_name]))
    .map((item) => item.model_feature_name);
  const snapshotDefaultedFeatures: string[] = [];
  const snapshotDoctorProvidedFeatures = snapshotProvidedFeatureNames;
  const snapshotArtifactComplete = snapshotProvidedFeatureNames.length === featureRows.length;
  const snapshotAssessmentStatus = snapshotArtifactComplete && snapshotMissingRequiredFeatures.length === 0
    ? 'ready_for_inference'
    : 'insufficient_data_for_assessment';
  const snapshotInsufficient = snapshotAssessmentStatus !== 'ready_for_inference';
  const snapshotFeatureCount = featureRows.length;

  async function handleFillValidationBaseline() {
    setSnapshotValues(buildSyntheticBaseline(featureRows));
    setSnapshotValidationOnly(true);
    setSnapshotNoticeType('info');
    setSnapshotNotice('已填充验证用示例值，请检查后创建输入快照。');
  }

  function handleClearSnapshotValues() {
    setSnapshotValues({});
    setSnapshotValidationOnly(false);
    setSnapshotNoticeType('info');
    setSnapshotNotice('已清空特征输入。');
  }

  async function handleCreateSnapshot() {
    if (!selectedVersionId || !selectedVersion) {
      setSnapshotNoticeType('error');
      setSnapshotNotice('请选择模型版本后再创建输入快照。');
      return;
    }
    if (!schema) {
      setSnapshotNoticeType('error');
      setSnapshotNotice('模型输入 schema 尚未加载，请稍后重试。');
      return;
    }
    const missingRequired = snapshotMissingRequiredFeatures;
    const missingAll = snapshotMissingFeatures;
    setSnapshotSubmitting(true);
    setSnapshotNotice('');
    try {
      const payload: ModelInputSnapshotCreatePayload = {
        trace_id: snapshotTraceId || caseRecord?.trace_id || 'trace_manual_snapshot_' + Date.now(),
        model_version_id: selectedVersionId,
        model_input_schema_id: schema.model_input_schema_id,
        disease_task_feature_set_id: schema.disease_task_feature_set_id || 'cap_cop_clinical_feature_set_v1',
        preprocess_artifact_ref: schema.preprocess_artifact_ref || 'clinical_tabular_standardization_v1.json',
        mapped_features: snapshotMappedFeatures,
        missing_features: missingAll,
        defaulted_features: snapshotDefaultedFeatures,
        doctor_provided_features: snapshotDoctorProvidedFeatures,
        source_refs: [
          {
            source: 'manual_frontend_entry',
            validation_only: snapshotValidationOnly,
            feature_count: snapshotDoctorProvidedFeatures.length,
          },
        ],
        validation_status: snapshotArtifactComplete && missingRequired.length === 0 ? 'ready_for_inference' : 'insufficient_data_for_assessment',
        current_assessment_status: snapshotArtifactComplete && missingRequired.length === 0 ? 'ready_for_inference' : 'insufficient_data_for_assessment',
        insufficient_data_for_assessment: !(snapshotArtifactComplete && missingRequired.length === 0),
        runtime_stub: true,
        not_for_diagnosis: true,
      };
      const created = await createModelInputSnapshot(caseId, payload);
      if (missingRequired.length > 0) {
        setSnapshotNoticeType('warning');
        setSnapshotNotice('输入快照已保存：' + created.input_snapshot_id + '；但缺少 required feature，当前数据不足以判断，不能运行 shadow。');
      } else {
        setSnapshotNoticeType('success');
        setSnapshotNotice('输入快照已创建：' + created.input_snapshot_id);
      }
      const response = await listModelInputSnapshotsByCase(caseId);
      setSnapshotRows(response.items || []);
    } catch (error) {
      setSnapshotNoticeType('error');
      setSnapshotNotice(translateError(error));
    } finally {
      setSnapshotSubmitting(false);
    }
  }

  async function copySnapshotId(snapshotId: string) {
    try {
      await navigator.clipboard.writeText(snapshotId);
      setSnapshotNoticeType('success');
      setSnapshotNotice('已复制 snapshot_id：' + snapshotId);
    } catch {
      setSnapshotNoticeType('error');
      setSnapshotNotice('复制失败，请手动复制 snapshot_id。');
    }
  }

  async function handleRunShadow(snapshot: ModelInputSnapshotSummaryItem) {
    if (snapshot.validation_status !== 'ready_for_inference' || snapshot.insufficient_data_for_assessment) {
      setShadowRunNoticeType('warning');
      setShadowRunNotice('缺少 required feature，不能运行 shadow。');
      return;
    }
    setShadowRunningSnapshotId(snapshot.input_snapshot_id);
    setShadowRunNotice('');
    setShadowRunResult(null);
    setShadowRunOutputId('');
    try {
      const response = await runClinicalMlpFold5OneShotShadow(caseId, {
        input_snapshot_id: snapshot.input_snapshot_id,
        trace_id: snapshot.trace_id || caseRecord?.trace_id || snapshotTraceId || 'trace_manual_snapshot_' + Date.now(),
        dry_run_label: 'frontend_manual_snapshot',
      });
      const outputs = await getShadowRunOutputs(response.shadow_run_id).catch(() => ({ items: [] }));
      const output = outputs.items?.[0] || null;
      const mergedResult: ControlledShadowClinicalMlpFold5OneShotResponse = {
        ...response,
        candidate_label: response.candidate_label || output?.candidate_label || null,
      };
      setShadowRunResult(mergedResult);
      setShadowRunOutputId(output?.output_id || '');
      setShadowRunNoticeType('success');
      setShadowRunNotice(
        'shadow_run_id: ' +
          response.shadow_run_id +
          (output?.output_id ? ' · output_id: ' + output.output_id : '') +
          (mergedResult.candidate_label ? ' · candidate_label: ' + mergedResult.candidate_label : '')
      );
    } catch (error) {
      setShadowRunNoticeType('error');
      setShadowRunNotice(translateError(error));
    } finally {
      setShadowRunningSnapshotId('');
    }
  }

  if (loadingPage) {
    return (
      <div style={{ minHeight: 240, display: 'grid', placeItems: 'center' }}>
        <Spin spinning>
          <div style={{ width: 320, height: 80 }} />
        </Spin>
      </div>
    );
  }

  if (pageError) {
    return (
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <Typography.Title level={4} style={{ margin: 0 }}>模型输入预览</Typography.Title>
        <Alert type='error' showIcon message={pageError} description='请先返回病例列表，确认病例与模型注册数据可用。' />
        <Space wrap>
          <Button type='primary' href='/cases'>返回病例列表</Button>
          <Button href='/dashboard'>返回工作台</Button>
        </Space>
      </Space>
    );
  }

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>模型输入预览</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}{caseRecord?.case_no ? ' · ' + caseRecord.case_no : ''}</Typography.Text>

      <Alert
        type='info'
        showIcon
        message='当前仅做模型输入预览与规则校验'
        description='本页只展示病例数据映射到模型输入 schema 后的预览和校验结果。LLM 或前端参数不能绕过 required feature 校验，也不能 silent fallback。'
      />
      <Alert
        type='warning'
        showIcon
        message='字段契约待复核 / schema_unverified'
        description='当前 36 个前端输入字段尚未确认等同于 fold5 真实训练输入。CAP/COP 原表与当前输入 schema 存在字段差异，Sex 等字段编码未验证。请勿将当前 shadow 输出理解为可靠模型评估。'
        style={{ marginTop: 16 }}
      />

      <Card title='病例上下文' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }} extra={caseRecord?.trace_id ? <Link href={'/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(caseRecord.trace_id)}>查看溯源</Link> : null}>
        <Descriptions bordered size='small' column={2}>
          <Descriptions.Item label='病种任务'>{caseRecord?.disease_task || '-'}</Descriptions.Item>
          <Descriptions.Item label='Trace / 溯源 ID'>{caseRecord?.trace_id || '-'}</Descriptions.Item>
          <Descriptions.Item label='病例编号'>{caseRecord?.case_no || '-'}</Descriptions.Item>
          <Descriptions.Item label='主诉'>{caseRecord?.chief_complaint || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title='候选模型与模型选择预览' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
        <Spin spinning={selectionLoading}>
          <Space direction='vertical' size={12} style={{ width: '100%' }}>
            {selectionError ? <Alert type='error' showIcon message={selectionError} /> : null}
            <Alert
              type={selectionRequired ? 'warning' : 'success'}
              showIcon
              message={selectionRequired ? '多模型候选，需要模型选择预览' : '单模型候选，不做模型选择，只做输入校验'}
              description={selectionRequired ? '当前病种任务下存在多个候选模型，系统先给出候选匹配结果，再做输入规则校验。' : '当前只存在单个候选模型，系统不会做模型选择。'}
            />
            <Descriptions bordered size='small' column={3}>
              <Descriptions.Item label='病种任务'>{selectionPreview?.disease_task || caseRecord?.disease_task || '-'}</Descriptions.Item>
              <Descriptions.Item label='是否需要模型选择'>{selectionRequired ? '是' : '否'}</Descriptions.Item>
              <Descriptions.Item label='选择原因'>{selectionReason || '-'}</Descriptions.Item>
              <Descriptions.Item label='候选模型数'>{candidateCount}</Descriptions.Item>
              <Descriptions.Item label='当前候选'>{selectedCandidate ? selectedCandidate.model_name + ' / ' + selectedCandidate.version_label : '-'}</Descriptions.Item>
              <Descriptions.Item label='选中模型版本 ID'>{selectedCandidate?.model_version_id || selectedVersionId || '-'}</Descriptions.Item>
            </Descriptions>
            <Table
              rowKey='model_version_id'
              pagination={false}
              dataSource={selectionRows}
              scroll={{ x: 'max-content' }}
              columns={[
                { title: '模型名称', dataIndex: 'model_name' },
                { title: '版本', dataIndex: 'version_label' },
                { title: '模型版本 ID', dataIndex: 'model_version_id' },
                { title: '生命周期', dataIndex: 'lifecycle_status', render: (value: string) => value || '-' },
                { title: '支持模态', dataIndex: 'supported_modalities', render: (value: string[]) => renderTags(value, 'blue') },
                { title: '特征覆盖率', dataIndex: 'feature_completeness', render: (value: number | null | undefined) => (typeof value === 'number' ? value.toFixed(2) : '-') },
                { title: '缺少的必需特征', dataIndex: 'missing_required_features', render: (value: string[]) => renderTags(value, 'red') },
                { title: '可默认特征', dataIndex: 'defaultable_features', render: (value: string[]) => renderTags(value, 'green') },
                { title: '当前评估状态', dataIndex: 'current_assessment_status', render: (value: string) => value || '-' },
              ]}
            />
          </Space>
        </Spin>
      </Card>

      <Card title='模型输入 schema' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }} extra={<Space wrap><Tag color='orange'>schema_unverified</Tag><Select style={{ width: 420 }} value={selectedVersionId} options={versionOptions.map((item) => ({ value: item.version_id, label: item.model_name + ' · ' + item.version_label + ' · ' + item.version_id.slice(0, 8) }))} onChange={(value) => setSelectedVersionId(String(value))} />{selectedVersion ? <Tag color='blue'>{selectedVersion.model_name}</Tag> : null}<Tag color='geekblue'>{selectedVersionId}</Tag></Space>}>
        <Descriptions bordered size='small' column={3}>
          <Descriptions.Item label='病种任务特征集'>{schema?.disease_task_feature_set_name || schema?.disease_task_feature_set_key || '-'}</Descriptions.Item>
          <Descriptions.Item label='模型输入 schema'>{schema?.model_input_schema_name || schema?.model_input_schema_key || '-'}</Descriptions.Item>
          <Descriptions.Item label='特征数'>{schema?.feature_count ?? featureRows.length ?? 0}</Descriptions.Item>
          <Descriptions.Item label='必需数'>{requirements.filter((item) => item.required).length}</Descriptions.Item>
          <Descriptions.Item label='可默认数'>{requirements.filter((item) => item.defaultable).length}</Descriptions.Item>
          <Descriptions.Item label='支持模态'>{renderTags(schema?.supported_modalities, 'blue')}</Descriptions.Item>
          <Descriptions.Item label='支持病种'>{renderTags(schema?.supported_disease_tasks, 'purple')}</Descriptions.Item>
          <Descriptions.Item label='预处理制品引用'>{schema?.preprocess_artifact_ref || '-'}</Descriptions.Item>
          <Descriptions.Item label='生命周期'>{schema?.lifecycle_status || '-'}</Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 16 }}>
          <Alert
            type='info'
            showIcon
            message='CAP/COP 临床 MLP 输入说明'
            description='cap_cop_clinical_feature_set_v1 是训练时的 36 个 CAP/COP 模型输入特征；原始脱敏 CSV 里还保留 Height、Weight、BMI、Hospitalization_duration 等原表字段，它们不等于当前 36-feature schema。Sex / Dyspnea / SmokingHistory 属于模型输入字段，本页按 schema 类型展示为选择控件；Sex 的训练编码待与训练 schema 复核。下一步需要按 clinical_tabular_standardization_v1.json 的 36 列顺序重建/核对前端字段。在完成 preprocess artifact 对齐前，当前页面只作为输入链路演示。不要用当前输入结果做医学判断。'
          />
        </div>
        <div style={{ marginTop: 16 }}>
          <Table
            rowKey='model_feature_name'
            pagination={false}
            dataSource={featureRows}
            scroll={{ x: 'max-content' }}
            columns={[
              { title: '顺序', dataIndex: 'feature_order', width: 80 },
              {
                title: '字段说明',
                dataIndex: 'model_feature_name',
                width: 260,
                render: (_: string, item: ModelInputFeatureRequirement) => (
                  <Space direction='vertical' size={2}>
                    <Typography.Text strong>{getFeatureDisplayName(item)}</Typography.Text>
                    <Typography.Text type='secondary' style={{ fontSize: 12 }}>模型字段：{item.model_feature_name}</Typography.Text>
                    <Typography.Text type='secondary' style={{ fontSize: 12 }}>原表字段：{getSourceFieldDisplayName(item)}</Typography.Text>
                    <Space wrap size={6}>
                      <Tag color={getFieldSourceStatusColor(getFieldSourceStatus(item))}>{getFieldSourceStatusLabel(getFieldSourceStatus(item))}</Tag>
                      {item.model_feature_name === 'Sex' ? <Tag color='gold'>CSV/artifact 未确认</Tag> : null}
                      {item.model_feature_name === 'Sex' ? <Tag color='orange'>编码未验证</Tag> : null}
                      {item.model_feature_name === 'Sex' ? <Tag color='gold'>性别编码待与训练 schema 复核</Tag> : null}
                      {item.model_feature_name === 'Striated_shadow.1' ? <Tag color='orange'>历史 schema 保留字段</Tag> : null}
                    </Space>
                  </Space>
                ),
              },
              { title: '类型', dataIndex: 'feature_type', width: 120, render: (_: string, item: ModelInputFeatureRequirement) => <Tag>{getFeatureTypeLabel(item)}</Tag> },
              { title: '字段来源状态', width: 170, render: (_: unknown, item: ModelInputFeatureRequirement) => <Tag color={getFieldSourceStatusColor(getFieldSourceStatus(item))}>{getFieldSourceStatusLabel(getFieldSourceStatus(item))}</Tag> },
              { title: '原表字段', dataIndex: 'source_clinical_field', width: 180 },
              { title: '必需', dataIndex: 'required', width: 100, render: (value: boolean) => renderFeatureBool(value) },
              { title: '可默认', dataIndex: 'defaultable', width: 110, render: (value: boolean) => renderFeatureBool(value) },
              { title: '缺失处理', dataIndex: 'missing_value_policy', render: (value: string | null | undefined) => value || '-' },
              { title: '默认处理', dataIndex: 'default_strategy', render: (value: string | null | undefined) => value || '-' },
              { title: '单位', dataIndex: 'unit', render: (value: string | null | undefined) => value || '-' },
              { title: '说明', dataIndex: 'notes', render: (value: string | null | undefined) => value || '-' },
              {
                title: '输入控件 / 提交值',
                width: 180,
                render: (_: unknown, item: ModelInputFeatureRequirement) => (
                  <Space wrap size={6}>
                    <Tag color={item.feature_type === 'numeric' ? 'blue' : item.feature_type === 'boolean' ? 'green' : 'purple'}>
                      {item.feature_type === 'numeric' ? '数值' : item.feature_type === 'boolean' ? '二值' : item.feature_type === 'categorical' ? '分类' : '待确认'}
                    </Tag>
                    {item.model_feature_name === 'Sex' ? <Tag color='geekblue'>男/女</Tag> : null}
                    {item.model_feature_name === 'Striated_shadow.1' ? <Tag color='orange'>历史保留</Tag> : null}
                  </Space>
                ),
              },
            ]}
          />
        </div>
      </Card>


      <Card
        title='临床表格输入契约 / artifact-order 映射'
        style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}
      >
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Alert
            type='warning'
            showIcon
            message='临床表格字段必须先映射到训练 artifact 的 36-feature order'
            description='原始临床表格字段、CSV 列顺序、产品表单顺序和 case_model_input_snapshot 的 key 顺序都不能直接当作模型输入。只有把每个字段明确映射到 artifact 顺序后，snapshot 才能进入 ready_for_inference；否则保持 schema_unverified / insufficient_data_for_assessment。缺失字段不能 silent fallback，默认值也不能自动补齐后继续推理。'
          />
          <Descriptions bordered size='small' column={2}>
            <Descriptions.Item label='原始临床表格字段'>CSV / 手工录入 / 导入粘贴的源列名</Descriptions.Item>
            <Descriptions.Item label='训练 artifact 36-feature order'>按 feature_order 排列的训练输入顺序</Descriptions.Item>
            <Descriptions.Item label='Snapshot'>case_model_input_snapshot，仅保存映射后的输入快照</Descriptions.Item>
            <Descriptions.Item label='当前状态'>schema_unverified</Descriptions.Item>
          </Descriptions>
          <Alert
            type='info'
            showIcon
            message='CSV 粘贴 / 导入只做表头与样例行解析'
            description='下面的输入框只解析表头和第一行样例值，不会直接创建可推理 snapshot。系统会显示每个原始列名映射到哪个 36-feature，以及是否已验证。未映射字段会标记为“未验证 / 不可用于模型”。'
          />
          <Input.TextArea
            value={artifactCsvText}
            onChange={(event) => { setArtifactCsvText(event.target.value); setArtifactCsvPreviewReady(false); }}
            placeholder={'粘贴 CSV 表头与一行样例，例如：\nAge,Sex,Temperature\n68,male,37.2'}
            autoSize={{ minRows: 4, maxRows: 10 }}
          />
          <Space wrap>
            <Button type='primary' onClick={() => setArtifactCsvPreviewReady(true)} disabled={!artifactCsvText.trim()}>解析 CSV 表头</Button>
            <Button onClick={() => { setArtifactCsvText(''); setArtifactCsvPreviewReady(false); }}>清空</Button>
          </Space>
          <Typography.Text type='secondary'>
            这里只做契约预览：原始列名 → 训练 artifact 顺序 → snapshot。未验证字段不会自动进入模型输入。
          </Typography.Text>
          {artifactCsvText.trim() ? (
            <Table
              rowKey='raw_column'
              pagination={false}
              size='small'
              scroll={{ x: 'max-content' }}
              dataSource={artifactCsvPreviewReady ? artifactCsvMappingRows : []}
              locale={{ emptyText: artifactCsvPreviewReady ? '暂无可解析列，请检查 CSV 文本' : '点击“解析 CSV 表头”后查看映射结果' }}
              columns={[
                { title: '原始列名', dataIndex: 'raw_column', width: 220 },
                { title: '样例值', dataIndex: 'sample_value', width: 160 },
                { title: '目标 feature', dataIndex: 'target_feature', width: 180 },
                { title: 'artifact 顺序', dataIndex: 'artifact_order', width: 120, render: (value: number | null) => (value === null ? '-' : value) },
                { title: '映射状态', dataIndex: 'status', width: 180, render: (value: string) => <Tag color={value === '已验证' ? 'green' : 'orange'}>{value}</Tag> },
                { title: '训练字段映射说明', dataIndex: 'source_field', render: (value: string) => value || '-' },
              ]}
            />
          ) : null}
        </Space>
      </Card>

      <Card
        title='手工录入 CAP/COP 特征并创建输入快照'
        extra={
          <Space wrap size={6}>
            <Tag color='orange'>schema_unverified</Tag>
            <Tag color='red'>非诊断</Tag>
            <Tag color='orange'>测试/开发记录</Tag>
            <Tag color={snapshotValidationOnly ? 'geekblue' : 'default'}>{snapshotValidationOnly ? '仅验证示例' : '手工录入'}</Tag>
          </Space>
        }
        style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}
      >
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Alert
            type='info'
            showIcon
            message='这里录入的是 CAP/COP clinical MLP 的模型输入特征，不是病例基础信息。'
            description='创建 snapshot 只保留输入 provenance，不会运行模型。保存后 snapshot 若为 ready_for_inference，才可以点击下面的受控 shadow 按钮。'
          />
          {snapshotNotice ? <Alert type={snapshotNoticeType} showIcon message={snapshotNotice} /> : null}
          <Descriptions bordered size='small' column={3}>
            <Descriptions.Item label='Trace / 溯源 ID'>
              <Input
                value={snapshotTraceId}
                onChange={(event) => setSnapshotTraceId(event.target.value)}
                placeholder='trace_manual_snapshot_...'
              />
            </Descriptions.Item>
            <Descriptions.Item label='模型版本 ID'>{selectedVersionId || '-'}</Descriptions.Item>
            <Descriptions.Item label='特征数'>{snapshotFeatureCount}</Descriptions.Item>
            <Descriptions.Item label='校验状态'>{snapshotAssessmentStatus}</Descriptions.Item>
            <Descriptions.Item label='当前评估状态'>{snapshotAssessmentStatus}</Descriptions.Item>
            <Descriptions.Item label='数据不足'>{snapshotInsufficient ? '是' : '否'}</Descriptions.Item>
          </Descriptions>
          <Space wrap>
            <Button type='primary' onClick={handleFillValidationBaseline} disabled={featureRows.length === 0}>填充验证用示例值</Button>
            <Button onClick={handleClearSnapshotValues}>清空</Button>
            <Button type='primary' onClick={handleCreateSnapshot} loading={snapshotSubmitting} disabled={!selectedVersionId || featureRows.length === 0}>
              创建输入快照
            </Button>
          </Space>
          <Typography.Text type='secondary'>
            当前已填：{snapshotProvidedFeatureNames.length} / {snapshotFeatureCount}。缺少 required feature 时仍可保存，但状态会显示为“当前数据不足以判断”，不能运行 shadow。
          </Typography.Text>
          <Space wrap size={6}>
            <Tag color='orange'>schema_unverified</Tag>
            <Tag color='red'>旁路审计</Tag>
            <Tag color='red'>非诊断</Tag>
            <Tag color='red'>非正式推荐</Tag>
            <Tag color='orange'>概率未校准</Tag>
            <Tag color='gold'>需要医生复核</Tag>
          </Space>
          <Table
            rowKey='model_feature_name'
            pagination={false}
            loading={previewLoading}
            dataSource={featureRows}
            scroll={{ x: 'max-content', y: 520 }}
            columns={[
              { title: '顺序', dataIndex: 'feature_order', width: 80 },
              {
                title: '字段说明',
                dataIndex: 'model_feature_name',
                width: 260,
                render: (_: string, item: ModelInputFeatureRequirement) => (
                  <Space direction='vertical' size={2}>
                    <Typography.Text strong>{getFeatureDisplayName(item)}</Typography.Text>
                    <Typography.Text type='secondary' style={{ fontSize: 12 }}>模型字段：{item.model_feature_name}</Typography.Text>
                    <Typography.Text type='secondary' style={{ fontSize: 12 }}>原表字段：{getSourceFieldDisplayName(item)}</Typography.Text>
                    <Space wrap size={6}>
                      <Tag color={getFieldSourceStatusColor(getFieldSourceStatus(item))}>{getFieldSourceStatusLabel(getFieldSourceStatus(item))}</Tag>
                      {item.model_feature_name === 'Sex' ? <Tag color='gold'>CSV/artifact 未确认</Tag> : null}
                      {item.model_feature_name === 'Sex' ? <Tag color='orange'>编码未验证</Tag> : null}
                      {item.model_feature_name === 'Sex' ? <Tag color='gold'>性别编码待与训练 schema 复核</Tag> : null}
                      {item.model_feature_name === 'Striated_shadow.1' ? <Tag color='orange'>历史 schema 保留字段</Tag> : null}
                    </Space>
                  </Space>
                ),
              },
              { title: '原表字段', dataIndex: 'source_clinical_field', width: 180 },
              { title: '类型', dataIndex: 'feature_type', width: 120, render: (_: string, item: ModelInputFeatureRequirement) => <Tag>{getFeatureTypeLabel(item)}</Tag> },
              { title: '字段来源状态', width: 170, render: (_: unknown, item: ModelInputFeatureRequirement) => <Tag color={getFieldSourceStatusColor(getFieldSourceStatus(item))}>{getFieldSourceStatusLabel(getFieldSourceStatus(item))}</Tag> },
              { title: '必需', dataIndex: 'required', width: 100, render: (value: boolean) => (value ? <Tag color='red'>必需</Tag> : <Tag>可选</Tag>) },
              { title: '可默认', dataIndex: 'defaultable', width: 110, render: (value: boolean) => (value ? <Tag color='green'>可默认</Tag> : <Tag>不可默认</Tag>) },
              { title: '缺失处理', dataIndex: 'missing_value_policy', width: 180, render: (value: string | null | undefined) => value || '-' },
              { title: '单位', dataIndex: 'unit', width: 100, render: (value: string | null | undefined) => value || '-' },
              { title: '说明', dataIndex: 'notes', width: 260, render: (value: string | null | undefined) => value || '-' },
              {
                title: '输入值',
                width: 180,
                fixed: 'right',
                render: (_: unknown, item: ModelInputFeatureRequirement) => (
                  <div style={{ minWidth: 150 }}>
                    {renderFeatureInput(item, snapshotValues[item.model_feature_name] ?? null, (next) => {
                      setSnapshotValues((current) => ({
                        ...current,
                        [item.model_feature_name]: next,
                      }));
                    })}
                  </div>
                ),
              },
            ]}
          />
        </Space>
      </Card>

      <Card title='已创建的输入快照' extra={<Tag color='blue'>病例级输入快照</Tag>} style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
          <Table
            rowKey='input_snapshot_id'
            loading={snapshotLoading}
            pagination={false}
            dataSource={snapshotRows}
            locale={{ emptyText: '暂无输入快照' }}
            scroll={{ x: 'max-content' }}
            columns={[
            { title: '输入快照 ID', dataIndex: 'input_snapshot_id', width: 220 },
            { title: 'Trace / 溯源 ID', dataIndex: 'trace_id', width: 200 },
            { title: '模型版本 ID', dataIndex: 'model_version_id', width: 220 },
            { title: '校验状态', dataIndex: 'validation_status', width: 180, render: (value: string) => statusLabel(value) },
            { title: '当前评估状态', dataIndex: 'current_assessment_status', width: 200, render: (value: string) => statusLabel(value) },
            { title: '数据不足', dataIndex: 'insufficient_data_for_assessment', width: 170, render: (value: boolean) => (value ? <Tag color='orange'>是</Tag> : <Tag color='green'>否</Tag>) },
            { title: '已映射特征数', dataIndex: 'mapped_feature_count', width: 140 },
            { title: '缺失特征数', dataIndex: 'missing_feature_count', width: 140 },
            { title: '创建时间', dataIndex: 'created_at', width: 220, render: (value: string | null | undefined) => value || '-' },
            {
              title: 'Shadow 入口',
              width: 360,
              fixed: 'right',
              render: (_: unknown, item: ModelInputSnapshotSummaryItem) => (
                <Space direction='vertical' size={4}>
                  <Space wrap size={6}>
            <Tag color='red'>旁路审计</Tag>
                    <Tag color='red'>非诊断</Tag>
                    <Tag color='red'>非正式推荐</Tag>
                    <Tag color='orange'>概率未校准</Tag>
                  </Space>
                  <Space wrap size={8}>
                    <Button type='link' onClick={() => copySnapshotId(item.input_snapshot_id)}>复制 snapshot_id</Button>
                      <Button
                        type='primary'
                        size='small'
                        onClick={() => handleRunShadow(item)}
                        loading={shadowRunningSnapshotId === item.input_snapshot_id}
                        disabled={schemaUnverified}
                      >
                        训练字段契约待复核，暂不运行 Shadow
                      </Button>
                    <Link href={'/cases/' + caseId + '/shadow-audit'}>查看 Shadow 审计</Link>
                  </Space>
                </Space>
              ),
            },
          ]}
        />
        {shadowRunNotice ? <Alert style={{ marginTop: 12 }} type={shadowRunNoticeType} showIcon message={shadowRunNotice} description={shadowRunResult ? (
          <Space direction='vertical' size={4}>
            <Typography.Text>Shadow 记录 ID：{shadowRunResult.shadow_run_id}</Typography.Text>
            <Typography.Text>状态：{statusLabel(shadowRunResult.status)}</Typography.Text>
            <Typography.Text>输出 ID：{shadowRunOutputId || '-'}</Typography.Text>
            <Typography.Text>旁路候选标签：{shadowRunResult.candidate_label || '-'}</Typography.Text>
            <Typography.Text>输入快照 ID：{shadowRunResult.input_snapshot_id}</Typography.Text>
            <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + encodeURIComponent(shadowRunResult.shadow_run_id)}>打开 Shadow 审计</Link>
          </Space>
        ) : null} /> : null}
      </Card>

      <Row gutter={16} style={{ width: '100%', maxWidth: '100%' }}>
        <Col xs={24} lg={12} style={{ minWidth: 0 }}>
          <Card title='模型输入预览' style={{ minWidth: 0, width: '100%', maxWidth: '100%' }} extra={<Space wrap><Tag color='blue'>模型版本 ID：{selectedVersionId || '-'}</Tag></Space>}>
            <Spin spinning={previewLoading}>
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                {previewError ? <Alert type='error' showIcon message={previewError} /> : null}
                <Descriptions bordered size='small' column={2}>
                  <Descriptions.Item label='当前评估状态'>{assessmentStatus}</Descriptions.Item>
                  <Descriptions.Item label='数据不足'>{insufficientData ? '当前数据不足以判断' : '否'}</Descriptions.Item>
                  <Descriptions.Item label='缺少的必需特征'>{renderTags(missingRequiredFeatures, 'red')}</Descriptions.Item>
                  <Descriptions.Item label='可默认特征'>{renderTags(defaultableFeatures, 'green')}</Descriptions.Item>
                  <Descriptions.Item label='缺失特征' span={2}>{renderTags(missingFeatures, 'gold')}</Descriptions.Item>
                  <Descriptions.Item label='已提供特征' span={2}>{renderTags(providedFeatures, 'blue')}</Descriptions.Item>
                  <Descriptions.Item label='建议医生问题' span={2}>{doctorQuestions.length ? <Space direction='vertical' size={4}>{doctorQuestions.map((item) => <Tag key={item} color='geekblue'>{item}</Tag>)}</Space> : '-'}</Descriptions.Item>
                </Descriptions>
              </Space>
            </Spin>
          </Card>
        </Col>
        <Col xs={24} lg={12} style={{ minWidth: 0 }}>
          <Card title='模型输入校验' style={{ minWidth: 0, width: '100%', maxWidth: '100%' }}>
            <Spin spinning={previewLoading}>
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Descriptions bordered size='small' column={2}>
                  <Descriptions.Item label='当前评估状态'>{validationResult?.current_assessment_status || '-'}</Descriptions.Item>
                  <Descriptions.Item label='数据不足'>{validationResult?.insufficient_data_for_assessment ? '当前数据不足以判断' : '否'}</Descriptions.Item>
                  <Descriptions.Item label='缺少的必需特征'>{renderTags(validationResult?.missing_required_features || [], 'red')}</Descriptions.Item>
                  <Descriptions.Item label='可默认特征'>{renderTags(validationResult?.defaultable_features || [], 'green')}</Descriptions.Item>
                  <Descriptions.Item label='缺失特征' span={2}>{renderTags(validationResult?.missing_features || [], 'gold')}</Descriptions.Item>
                  <Descriptions.Item label='已提供特征' span={2}>{renderTags(getProvidedFeatures(validationResult), 'blue')}</Descriptions.Item>
                  <Descriptions.Item label='建议医生问题' span={2}>{getMissingRequiredQuestions(validationResult).length ? <Space direction='vertical' size={4}>{getMissingRequiredQuestions(validationResult).map((item) => <Tag key={item} color='geekblue'>{item}</Tag>)}</Space> : '-'}</Descriptions.Item>
                </Descriptions>
              </Space>
            </Spin>
          </Card>
        </Col>
      </Row>

      <Card title='使用说明' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
        <Space direction='vertical' size={8}>
          <Typography.Text>1. 手工录入区和 CSV 契约区都必须最终映射到训练 artifact 的 36-feature order。2. 创建 case_model_input_snapshot 时，只有 36 个字段全部明确且 required feature 不缺失，才能进入 ready_for_inference。3. snapshot 为“可用于 Shadow 评估”时，才可以手动点击“运行 CAP/COP Shadow 评估”。4. 该按钮只会调用受控 clinical MLP fold5 shadow 路径，只写 shadow 审计。5. 结果请在 Shadow 审计页查看。6. 它不是临床结论，也不会写入病例证据链。
7. 原始临床表格字段、CSV 列顺序和 snapshot key 顺序不能直接当作模型输入。8. disease_task_feature_set 是病种任务特征集合，不是全局病例表结构。9. 缺少 required feature 时不能 silent fallback，只能走缺失值咨询、明确默认策略或 insufficient_data_for_assessment。10. LLM 和前端参数不能绕过后端模型输入校验。</Typography.Text>
        </Space>
      </Card>
    </Space>
  );
}



