
'use client';

import Link from 'next/link';
import axios from 'axios';
import { use, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Col, Descriptions, Row, Select, Space, Spin, Table, Tag, Typography } from 'antd';
import {
  getModel,
  getModelFeatureRequirements,
  getModelInputSchema,
  listCases,
  listModels,
  previewCaseModelInput,
  previewModelSelection,
  validateCaseModelInput,
  type ModelInputFeatureRequirement,
  type ModelInputPreviewItem,
  type ModelInputPreviewPayload,
  type ModelInputSchemaResponse,
  type ModelSelectionCandidate,
  type ModelSelectionPreviewResponse,
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

  const featureRows = requirements;
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
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>模型输入预览</Typography.Title>
      <Typography.Text type='secondary'>病例：{caseId}{caseRecord?.case_no ? ' · ' + caseRecord.case_no : ''}</Typography.Text>

      <Alert
        type='info'
        showIcon
        message='当前仅做模型输入预览与规则校验'
        description='本页只展示病例数据映射到模型输入 schema 后的预览和校验结果。LLM 或前端参数不能绕过 required feature 校验，也不能 silent fallback。'
      />

      <Card title='病例上下文' extra={caseRecord?.trace_id ? <Link href={'/cases/' + caseId + '/lineage?trace_id=' + encodeURIComponent(caseRecord.trace_id)}>查看溯源</Link> : null}>
        <Descriptions bordered size='small' column={2}>
          <Descriptions.Item label='disease_task'>{caseRecord?.disease_task || '-'}</Descriptions.Item>
          <Descriptions.Item label='trace_id'>{caseRecord?.trace_id || '-'}</Descriptions.Item>
          <Descriptions.Item label='case_no'>{caseRecord?.case_no || '-'}</Descriptions.Item>
          <Descriptions.Item label='chief_complaint'>{caseRecord?.chief_complaint || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title='候选模型与模型选择预览'>
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
              <Descriptions.Item label='disease_task'>{selectionPreview?.disease_task || caseRecord?.disease_task || '-'}</Descriptions.Item>
              <Descriptions.Item label='selection_required'>{selectionRequired ? '是' : '否'}</Descriptions.Item>
              <Descriptions.Item label='selection_reason'>{selectionReason || '-'}</Descriptions.Item>
              <Descriptions.Item label='candidate_count'>{candidateCount}</Descriptions.Item>
              <Descriptions.Item label='selected_candidate'>{selectedCandidate ? selectedCandidate.model_name + ' / ' + selectedCandidate.version_label : '-'}</Descriptions.Item>
              <Descriptions.Item label='selected_model_version_id'>{selectedCandidate?.model_version_id || selectedVersionId || '-'}</Descriptions.Item>
            </Descriptions>
            <Table
              rowKey='model_version_id'
              pagination={false}
              dataSource={selectionRows}
              columns={[
                { title: '模型名称', dataIndex: 'model_name' },
                { title: '版本', dataIndex: 'version_label' },
                { title: '模型版本 ID', dataIndex: 'model_version_id' },
                { title: '生命周期', dataIndex: 'lifecycle_status', render: (value: string) => value || '-' },
                { title: '支持模态', dataIndex: 'supported_modalities', render: (value: string[]) => renderTags(value, 'blue') },
                { title: 'feature_completeness', dataIndex: 'feature_completeness', render: (value: number | null | undefined) => (typeof value === 'number' ? value.toFixed(2) : '-') },
                { title: 'missing_required_features', dataIndex: 'missing_required_features', render: (value: string[]) => renderTags(value, 'red') },
                { title: 'defaultable_features', dataIndex: 'defaultable_features', render: (value: string[]) => renderTags(value, 'green') },
                { title: 'current_assessment_status', dataIndex: 'current_assessment_status', render: (value: string) => value || '-' },
              ]}
            />
          </Space>
        </Spin>
      </Card>

      <Card title='模型输入 schema' extra={<Space wrap><Select style={{ width: 420 }} value={selectedVersionId} options={versionOptions.map((item) => ({ value: item.version_id, label: item.model_name + ' · ' + item.version_label + ' · ' + item.version_id.slice(0, 8) }))} onChange={(value) => setSelectedVersionId(String(value))} />{selectedVersion ? <Tag color='blue'>{selectedVersion.model_name}</Tag> : null}<Tag color='geekblue'>{selectedVersionId}</Tag></Space>}>
        <Descriptions bordered size='small' column={3}>
          <Descriptions.Item label='disease_task_feature_set'>{schema?.disease_task_feature_set_name || schema?.disease_task_feature_set_key || '-'}</Descriptions.Item>
          <Descriptions.Item label='model_input_schema'>{schema?.model_input_schema_name || schema?.model_input_schema_key || '-'}</Descriptions.Item>
          <Descriptions.Item label='feature_count'>{schema?.feature_count ?? featureRows.length ?? 0}</Descriptions.Item>
          <Descriptions.Item label='required_count'>{requirements.filter((item) => item.required).length}</Descriptions.Item>
          <Descriptions.Item label='defaultable_count'>{requirements.filter((item) => item.defaultable).length}</Descriptions.Item>
          <Descriptions.Item label='supported_modalities'>{renderTags(schema?.supported_modalities, 'blue')}</Descriptions.Item>
          <Descriptions.Item label='supported_disease_tasks'>{renderTags(schema?.supported_disease_tasks, 'purple')}</Descriptions.Item>
          <Descriptions.Item label='preprocess_artifact_ref'>{schema?.preprocess_artifact_ref || '-'}</Descriptions.Item>
          <Descriptions.Item label='lifecycle_status'>{schema?.lifecycle_status || '-'}</Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 16 }}>
          <Alert type='info' showIcon message='CAP/COP clinical MLP 输入说明' description='cap_cop_clinical_feature_set_v1 包含 36 个 CAP/COP 任务特征；Striated_shadow.1 是历史训练 schema 的保留字段，只属于 CAP/COP 模型输入契约。' />
        </div>
        <div style={{ marginTop: 16 }}>
          <Table
            rowKey='model_feature_name'
            pagination={false}
            dataSource={featureRows}
            columns={[
              { title: '顺序', dataIndex: 'feature_order', width: 80 },
              { title: '模型特征', dataIndex: 'model_feature_name', render: (value: string) => value === 'Striated_shadow.1' ? <Tag color='orange'>{value}</Tag> : value },
              { title: '来源临床字段', dataIndex: 'source_clinical_field' },
              { title: '必需', dataIndex: 'required', render: (value: boolean) => renderFeatureBool(value) },
              { title: '可默认', dataIndex: 'defaultable', render: (value: boolean) => renderFeatureBool(value) },
              { title: '缺失策略', dataIndex: 'missing_value_policy', render: (value: string | null | undefined) => value || '-' },
              { title: '默认策略', dataIndex: 'default_strategy', render: (value: string | null | undefined) => value || '-' },
              { title: '单位', dataIndex: 'unit', render: (value: string | null | undefined) => value || '-' },
              { title: '说明', dataIndex: 'notes', render: (value: string | null | undefined) => value || '-' },
            ]}
          />
        </div>
      </Card>

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title='模型输入预览' extra={<Space wrap><Tag color='blue'>model_version_id: {selectedVersionId || '-'}</Tag></Space>}>
            <Spin spinning={previewLoading}>
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                {previewError ? <Alert type='error' showIcon message={previewError} /> : null}
                <Descriptions bordered size='small' column={2}>
                  <Descriptions.Item label='current_assessment_status'>{assessmentStatus}</Descriptions.Item>
                  <Descriptions.Item label='insufficient_data_for_assessment'>{insufficientData ? '当前数据不足以判断' : '否'}</Descriptions.Item>
                  <Descriptions.Item label='missing_required_features'>{renderTags(missingRequiredFeatures, 'red')}</Descriptions.Item>
                  <Descriptions.Item label='defaultable_features'>{renderTags(defaultableFeatures, 'green')}</Descriptions.Item>
                  <Descriptions.Item label='missing_features' span={2}>{renderTags(missingFeatures, 'gold')}</Descriptions.Item>
                  <Descriptions.Item label='provided_features' span={2}>{renderTags(providedFeatures, 'blue')}</Descriptions.Item>
                  <Descriptions.Item label='suggested_doctor_questions' span={2}>{doctorQuestions.length ? <Space direction='vertical' size={4}>{doctorQuestions.map((item) => <Tag key={item} color='geekblue'>{item}</Tag>)}</Space> : '-'}</Descriptions.Item>
                </Descriptions>
              </Space>
            </Spin>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title='模型输入校验'>
            <Spin spinning={previewLoading}>
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Descriptions bordered size='small' column={2}>
                  <Descriptions.Item label='current_assessment_status'>{validationResult?.current_assessment_status || '-'}</Descriptions.Item>
                  <Descriptions.Item label='insufficient_data_for_assessment'>{validationResult?.insufficient_data_for_assessment ? '当前数据不足以判断' : '否'}</Descriptions.Item>
                  <Descriptions.Item label='missing_required_features'>{renderTags(validationResult?.missing_required_features || [], 'red')}</Descriptions.Item>
                  <Descriptions.Item label='defaultable_features'>{renderTags(validationResult?.defaultable_features || [], 'green')}</Descriptions.Item>
                  <Descriptions.Item label='missing_features' span={2}>{renderTags(validationResult?.missing_features || [], 'gold')}</Descriptions.Item>
                  <Descriptions.Item label='provided_features' span={2}>{renderTags(getProvidedFeatures(validationResult), 'blue')}</Descriptions.Item>
                  <Descriptions.Item label='suggested_doctor_questions' span={2}>{getMissingRequiredQuestions(validationResult).length ? <Space direction='vertical' size={4}>{getMissingRequiredQuestions(validationResult).map((item) => <Tag key={item} color='geekblue'>{item}</Tag>)}</Space> : '-'}</Descriptions.Item>
                </Descriptions>
              </Space>
            </Spin>
          </Card>
        </Col>
      </Row>

      <Card title='使用说明'>
        <Space direction='vertical' size={8}>
          <Typography.Text>1. 本页只做模型输入预览和规则校验，不触发模型运行。</Typography.Text>
          <Typography.Text>2. disease_task_feature_set 是病种任务特征集合，不是全局病例表结构。</Typography.Text>
          <Typography.Text>3. 缺少 required feature 时不能 silent fallback，只能走缺失值咨询、明确默认策略或 insufficient_data_for_assessment。</Typography.Text>
          <Typography.Text>4. LLM 和前端参数不能绕过后端模型输入校验。</Typography.Text>
        </Space>
      </Card>
    </Space>
  );
}
