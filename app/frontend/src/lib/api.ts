import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

type ApiMode = 'mock' | 'backend';

const API_MODE = (process.env.NEXT_PUBLIC_API_MODE || 'backend') as ApiMode;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/backend-api';

const ACCESS_TOKEN_KEY = 'medorion_access_token';
const REFRESH_TOKEN_KEY = 'medorion_refresh_token';
const CURRENT_USER_KEY = 'medorion_current_user';

const client = axios.create({ baseURL: API_BASE_URL, timeout: 10000 });

function getAccessToken(): string {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem(ACCESS_TOKEN_KEY) || '';
}

export function saveAuthTokens(accessToken: string, refreshToken: string) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearAuthTokens() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(CURRENT_USER_KEY);
}

export function getRefreshToken(): string {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem(REFRESH_TOKEN_KEY) || '';
}

export type CurrentUser = {
  user_id: string;
  username: string;
  display_name?: string | null;
  email?: string | null;
  role: string;
  is_active: boolean;
};

export function saveCurrentUser(user: CurrentUser) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
}

export function readCurrentUser(): CurrentUser | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(CURRENT_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as CurrentUser;
  } catch {
    return null;
  }
}

client.interceptors.request.use((config) => {
  config.headers.set('x-request-id', uuidv4());
  const token = getAccessToken();
  if (token) {
    config.headers.set('Authorization', 'Bearer ' + token);
  }
  return config;
});

function withTraceId(traceId?: string) {
  if (!traceId) return {};
  return { headers: { 'x-trace-id': traceId } };
}

function unwrapList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && Array.isArray((data as { items?: T[] }).items)) {
    return (data as { items: T[] }).items;
  }
  return [];
}

function unwrapItem<T>(data: unknown): T {
  if (data && typeof data === 'object' && 'item' in (data as Record<string, unknown>)) {
    return (data as { item: T }).item;
  }
  return data as T;
}

export const apiConfig = { mode: API_MODE, baseURL: API_BASE_URL };

const mock = {
  cases: [
    { case_id: 'case-001', patient_id: 'patient-001', disease_task: 'CAP', status: 'in_review', trace_id: 'trace-demo' },
    { case_id: 'case-002', patient_id: 'patient-002', disease_task: 'COP', status: 'awaiting_input', trace_id: 'trace-demo-2' },
  ],
  missingQueries: [
    {
      query_id: 'query-demo-pending',
      case_id: 'case-001',
      patient_id: 'patient-001',
      field_name: 'wbc',
      field_label: '白细胞',
      modality: 'lab',
      reason: 'demo',
      question_text: '请补充白细胞值',
      status: 'pending',
      trace_id: 'trace-demo',
      policy_version: 'v1',
      value_source: 'unknown',
      doctor_answer_text: null,
      doctor_answer_json: null,
      default_strategy_code: null,
      default_reason: null,
      default_value_json: null,
      created_at: '2026-06-02T00:00:00Z',
      updated_at: '2026-06-02T00:00:00Z',
    },
    {
      query_id: 'query-demo-answer',
      case_id: 'case-001',
      patient_id: 'patient-001',
      field_name: 'crp',
      field_label: 'C反应蛋白',
      modality: 'lab',
      reason: 'demo',
      question_text: '请补充CRP值',
      status: 'answered',
      trace_id: 'trace-demo',
      policy_version: 'v1',
      value_source: 'doctor_provided',
      doctor_answer_text: '11.2',
      doctor_answer_json: { value: 11.2 },
      default_strategy_code: null,
      default_reason: null,
      default_value_json: null,
      created_at: '2026-06-02T00:00:00Z',
      updated_at: '2026-06-02T00:00:00Z',
    },
    {
      query_id: 'query-demo-default',
      case_id: 'case-001',
      patient_id: 'patient-001',
      field_name: 'procalcitonin',
      field_label: '降钙素原',
      modality: 'lab',
      reason: 'demo',
      question_text: '请补充降钙素原值',
      status: 'default_applied',
      trace_id: 'trace-demo',
      policy_version: 'v1',
      value_source: 'default_applied',
      doctor_answer_text: null,
      doctor_answer_json: null,
      default_strategy_code: 'demo_default',
      default_reason: '演示默认策略',
      default_value_json: { value: 'demo-default' },
      created_at: '2026-06-02T00:00:00Z',
      updated_at: '2026-06-02T00:00:00Z',
    },
  ],
  recommendations: [
    { recommendation_id: 'rec-001', title: '示例推荐结果', risk_score: 0.78, trace_id: 'trace-demo' },
  ],
  qualityReviews: [
    {
      review_id: 'review-demo-001',
      case_id: 'case-001',
      trace_id: 'trace-demo',
      target_type: 'recommendation',
      target_id: 'rec-001',
      status: 'open',
      attribution: 'human_feedback',
      severity: 'medium',
      summary: '示例质控审查',
      related_feedback_id: 'feedback-demo-001',
      opened_by: 'dev_doctor',
      created_at: '2026-06-02T00:00:00Z',
      updated_at: '2026-06-02T00:00:00Z',
    },
  ],
};
export type InferenceTaskPayload = {
  patient_id: string;
  disease_agent: string;
  requested_task: string;
  model_version_policy: { mode: string; pinned_version?: string };
  inputs: Record<string, unknown>;
  missing_value_context: { pending_queries: unknown[] };
  idempotency_key: string;
};

export type InferenceTaskResponse = {
  trace_id?: string;
  task_id?: string;
  model_invocation_id?: string;
  model_version_id?: string;
  confidence?: number | Record<string, unknown> | null;
  uncertainty?: Record<string, unknown> | null;
  limitations?: unknown[];
  recommendation?: { evidence_refs?: unknown[] };
  model_service?: unknown;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
};

export type MissingValueQuery = {
  query_id: string;
  case_id: string;
  patient_id?: string | null;
  field_name: string;
  field_label?: string | null;
  modality?: string | null;
  reason?: string | null;
  question_text?: string | null;
  status?: string | null;
  trace_id?: string | null;
  policy_version?: string | null;
  value_source?: string | null;
  doctor_answer_text?: string | null;
  doctor_answer_json?: unknown | null;
  default_strategy_code?: string | null;
  default_reason?: string | null;
  default_value_json?: unknown | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type MissingValueListResponse = {
  items: MissingValueQuery[];
  total: number;
};

export type MissingValueCreatePayload = {
  field_name: string;
  field_label?: string;
  modality?: string;
  reason?: string;
  question_text?: string;
  trace_id?: string;
  value_source?: string;
  default_strategy_code?: string;
  default_reason?: string;
};

export type MissingValueAnswerPayload = {
  doctor_answer_text: string;
  doctor_answer_json?: unknown;
};

export type MissingValueDefaultPayload = {
  default_strategy_code: string;
  default_reason: string;
  default_value_json?: unknown;
};


export type DoctorFeedbackItem = {
  feedback_id: string;
  case_id: string;
  trace_id: string;
  recommendation_id?: string | null;
  feedback_type: string;
  feedback_text?: string | null;
  doctor_decision?: string | null;
  rating?: number | null;
  doctor_id?: string | null;
  learning_eligible: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type DoctorFeedbackListResponse = {
  items: DoctorFeedbackItem[];
  total: number;
};

export type DoctorFeedbackCreatePayload = {
  case_id: string;
  recommendation_id: string;
  trace_id?: string;
  feedback_type: string;
  feedback_text?: string;
  doctor_decision?: string;
  rating?: number | null;
  learning_eligible?: boolean;
};

export type DoctorFeedbackResponse = {
  status?: string;
  route: string;
  item: DoctorFeedbackItem;
};

export type QualityReviewItem = {
  review_id: string;
  case_id: string;
  trace_id: string;
  target_type: string;
  target_id: string;
  status: string;
  attribution: string;
  severity?: string | null;
  summary?: string | null;
  related_feedback_id?: string | null;
  opened_by?: string | null;
  actor_type?: string | null;
  actor_id?: string | null;
  attribution_confidence?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type QualityReviewListResponse = {
  items: QualityReviewItem[];
  total: number;
};

export type QualityReviewCreatePayload = {
  case_id: string;
  trace_id?: string;
  target_type: string;
  target_id: string;
  attribution: string;
  severity?: string;
  summary: string;
  related_feedback_id?: string;
};

export type QualityReviewResponse = {
  status?: string;
  route: string;
  item: QualityReviewItem;
};

export type ModelRegistryItem = {
  model_id: string;
  model_name: string;
  disease_agent: string;
  task_type: string;
  modality_scope: string[];
  owner_team: string;
  description?: string | null;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  versions?: ModelVersionItem[];
};

export type ModelVersionItem = {
  version_id: string;
  model_id: string;
  version_label: string;
  approval_state: 'draft' | 'offline_evaluated' | 'approved' | 'shadow' | 'canary' | 'default' | 'deprecated' | 'archived' | string;
  contract_version?: string | null;
  artifact_ref?: string | null;
  input_schema?: Record<string, unknown> | null;
  output_schema?: Record<string, unknown> | null;
  metrics?: Record<string, unknown> | null;
  runtime_constraints?: Record<string, unknown> | null;
  notes?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  promoted_by?: string | null;
  promoted_at?: string | null;
  archived_at?: string | null;
  rollback_from_version_id?: string | null;
  published_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ModelListResponse = {
  items: ModelRegistryItem[];
  total: number;
};

export type ModelCreatePayload = {
  model_name: string;
  disease_agent: string;
  task_type: string;
  modality_scope: string[];
  owner_team: string;
  description?: string;
};

export type ModelCreateResponse = {
  status?: string;
  route: string;
  item: ModelRegistryItem;
};

export type ModelVersionCreatePayload = {
  version_label: string;
  artifact_ref: string;
  metrics?: Record<string, unknown>;
  runtime_constraints?: Record<string, unknown>;
  notes?: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
};

export type ModelVersionResponse = {
  status?: string;
  route: string;
  item: ModelVersionItem;
};

export type ModelVersionEvaluationsResponse = {
  status?: string;
  route: string;
  item: Record<string, unknown>;
};

export type TraceEventItem = {
  event_type?: string;
  source_record_id?: string | null;
  payload?: {
    recommendation_id?: string | null;
  };
};

export async function login(username: string, password: string): Promise<LoginResponse> {
  const data = (await client.post('/api/v1/auth/login', { username, password })).data as LoginResponse;
  if (data?.access_token && data?.refresh_token) {
    saveAuthTokens(data.access_token, data.refresh_token);
  }
  return data;
}

export async function logout() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearAuthTokens();
    return;
  }
  try {
    await client.post('/api/v1/auth/logout', { refresh_token: refreshToken });
  } finally {
    clearAuthTokens();
  }
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const data = (await client.get('/api/v1/auth/me')).data as CurrentUser;
  saveCurrentUser(data);
  return data;
}

export async function refreshToken(): Promise<LoginResponse> {
  const rt = getRefreshToken();
  if (!rt) {
    throw new Error('missing_refresh_token');
  }
  const data = (await client.post('/api/v1/auth/refresh', { refresh_token: rt })).data as LoginResponse;
  if (data?.access_token && data?.refresh_token) {
    saveAuthTokens(data.access_token, data.refresh_token);
  }
  return data;
}

export async function getHealthReady() {
  if (API_MODE === 'mock') return { status: 'ready' };
  return (await client.get('/health/ready')).data;
}

export async function listCases(traceId?: string) {
  if (API_MODE === 'mock') return mock.cases;
  const data = (await client.get('/api/v1/cases', withTraceId(traceId))).data;
  return unwrapList(data);
}

export async function listMissingValueQueries(caseId: string, traceId?: string): Promise<MissingValueListResponse> {
  if (API_MODE === 'mock') {
    return { items: mock.missingQueries as MissingValueQuery[], total: mock.missingQueries.length };
  }
  const url = '/api/v1/cases/' + caseId + '/missing-values';
  const data = (await client.get(url, withTraceId(traceId))).data;
  const items = unwrapList<MissingValueQuery>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { items, total };
}

export async function createMissingValueQuery(caseId: string, payload: MissingValueCreatePayload, traceId?: string): Promise<MissingValueQuery> {
  const url = '/api/v1/cases/' + caseId + '/missing-values';
  if (API_MODE === 'mock') {
    return {
      query_id: 'query-demo-created',
      case_id: caseId,
      patient_id: 'patient-001',
      field_name: payload.field_name,
      field_label: payload.field_label || payload.field_name,
      modality: payload.modality || 'lab',
      reason: payload.reason || 'demo',
      question_text: payload.question_text || '请补充缺失值',
      status: 'pending',
      trace_id: payload.trace_id || traceId || 'trace-demo',
      policy_version: 'v1',
      value_source: payload.value_source || 'unknown',
      doctor_answer_text: null,
      doctor_answer_json: null,
      default_strategy_code: null,
      default_reason: null,
      default_value_json: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }
  const data = (await client.post(url, payload, withTraceId(traceId || payload.trace_id))).data;
  return unwrapItem<MissingValueQuery>(data);
}

export async function answerMissingValueQuery(caseId: string, queryId: string, payload: MissingValueAnswerPayload, traceId?: string): Promise<MissingValueQuery> {
  const url = '/api/v1/cases/' + caseId + '/missing-values/' + queryId + '/answer';
  if (API_MODE === 'mock') {
    return {
      query_id: queryId,
      case_id: caseId,
      patient_id: 'patient-001',
      field_name: 'wbc',
      field_label: '白细胞',
      modality: 'lab',
      reason: 'demo',
      question_text: '请补充白细胞值',
      status: 'answered',
      trace_id: traceId || 'trace-demo',
      policy_version: 'v1',
      value_source: 'doctor_provided',
      doctor_answer_text: payload.doctor_answer_text,
      doctor_answer_json: payload.doctor_answer_json ?? { value: payload.doctor_answer_text },
      default_strategy_code: null,
      default_reason: null,
      default_value_json: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }
  const data = (await client.post(url, payload, withTraceId(traceId))).data;
  return unwrapItem<MissingValueQuery>(data);
}

export async function applyDefaultMissingValueQuery(caseId: string, queryId: string, payload: MissingValueDefaultPayload, traceId?: string): Promise<MissingValueQuery> {
  const url = '/api/v1/cases/' + caseId + '/missing-values/' + queryId + '/apply-default';
  if (API_MODE === 'mock') {
    return {
      query_id: queryId,
      case_id: caseId,
      patient_id: 'patient-001',
      field_name: 'crp',
      field_label: 'C反应蛋白',
      modality: 'lab',
      reason: 'demo',
      question_text: '请补充CRP值',
      status: 'default_applied',
      trace_id: traceId || 'trace-demo',
      policy_version: 'v1',
      value_source: 'default_applied',
      doctor_answer_text: null,
      doctor_answer_json: null,
      default_strategy_code: payload.default_strategy_code,
      default_reason: payload.default_reason,
      default_value_json: payload.default_value_json || { value: 'demo-default' },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }
  const data = (await client.post(url, payload, withTraceId(traceId))).data;
  return unwrapItem<MissingValueQuery>(data);
}

export async function getMissingValues(caseId: string, traceId?: string) {
  const data = await listMissingValueQueries(caseId, traceId);
  return data.items;
}

export async function getRecommendations(caseId: string, traceId?: string) {
  if (API_MODE === 'mock') return mock.recommendations;
  const url = '/api/v1/cases/' + caseId + '/recommendations';
  const data = (await client.get(url, withTraceId(traceId))).data;
  return unwrapList(data);
}

export async function listFeedback(caseId: string): Promise<DoctorFeedbackListResponse> {
  if (API_MODE === 'mock') {
    const items = ((mock as { feedbacks?: DoctorFeedbackItem[] }).feedbacks || []).filter((item) => item.case_id === caseId) as DoctorFeedbackItem[];
    return { items, total: items.length };
  }
  const data = (await client.get('/api/v1/cases/' + caseId + '/feedback')).data;
  const items = unwrapList<DoctorFeedbackItem>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { items, total };
}

export async function listFeedbackByTrace(traceId: string): Promise<DoctorFeedbackListResponse> {
  if (API_MODE === 'mock') {
    const items = ((mock as { feedbacks?: DoctorFeedbackItem[] }).feedbacks || []).filter((item) => item.trace_id === traceId) as DoctorFeedbackItem[];
    return { items, total: items.length };
  }
  const data = (await client.get('/api/v1/feedback')).data;
  const items = unwrapList<DoctorFeedbackItem>(data).filter((item) => item.trace_id === traceId);
  return { items, total: items.length };
}

export async function createFeedback(payload: DoctorFeedbackCreatePayload): Promise<DoctorFeedbackItem> {
  if (API_MODE === 'mock') {
    const item: DoctorFeedbackItem = {
      feedback_id: 'feedback-demo-created',
      case_id: payload.case_id,
      trace_id: payload.trace_id || 'trace-demo',
      recommendation_id: payload.recommendation_id,
      feedback_type: payload.feedback_type,
      feedback_text: payload.feedback_text || null,
      doctor_decision: payload.doctor_decision || null,
      rating: payload.rating ?? null,
      doctor_id: 'dev_doctor',
      learning_eligible: payload.learning_eligible ?? true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    (mock as { feedbacks?: DoctorFeedbackItem[] }).feedbacks = [item, ...((mock as { feedbacks?: DoctorFeedbackItem[] }).feedbacks || [])];
    return item;
  }
  const data = (await client.post('/api/v1/feedback', payload)).data as DoctorFeedbackResponse;
  return unwrapItem<DoctorFeedbackItem>(data);
}

export async function listQualityReviews(caseId?: string): Promise<QualityReviewListResponse> {
  if (API_MODE === 'mock') {
    const items = (mock.qualityReviews as QualityReviewItem[]).filter((item) => (caseId ? item.case_id === caseId : true));
    return { items, total: items.length };
  }
  const url = caseId ? '/api/v1/cases/' + caseId + '/quality-reviews' : '/api/v1/quality-reviews';
  const data = (await client.get(url)).data;
  const items = unwrapList<QualityReviewItem>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { items, total };
}

export async function listQualityReviewsByCase(caseId: string) {
  return listQualityReviews(caseId);
}

export async function createQualityReview(payload: QualityReviewCreatePayload): Promise<QualityReviewItem> {
  if (API_MODE === 'mock') {
    const item: QualityReviewItem = {
      review_id: 'review-demo-created',
      case_id: payload.case_id,
      trace_id: payload.trace_id || 'trace-demo',
      target_type: payload.target_type,
      target_id: payload.target_id,
      status: 'open',
      attribution: payload.attribution,
      severity: payload.severity || 'medium',
      summary: payload.summary,
      related_feedback_id: payload.related_feedback_id || null,
      opened_by: 'dev_doctor',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    (mock as { qualityReviews?: QualityReviewItem[] }).qualityReviews = [item, ...((mock as { qualityReviews?: QualityReviewItem[] }).qualityReviews || [])];
    return item;
  }
  const data = (await client.post('/api/v1/quality-reviews', payload)).data as QualityReviewResponse;
  return unwrapItem<QualityReviewItem>(data);
}

export async function listModels(): Promise<ModelListResponse> {
  if (API_MODE === 'mock') {
    const items: ModelRegistryItem[] = [];
    return { items, total: items.length };
  }
  const data = (await client.get('/api/v1/model-registry')).data;
  const items = unwrapList<ModelRegistryItem>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { items, total };
}

export async function createModel(payload: ModelCreatePayload): Promise<ModelRegistryItem> {
  if (API_MODE === 'mock') {
    return {
      model_id: 'model-demo-created',
      model_name: payload.model_name,
      disease_agent: payload.disease_agent,
      task_type: payload.task_type,
      modality_scope: payload.modality_scope,
      owner_team: payload.owner_team,
      description: payload.description || null,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      versions: [],
    };
  }
  const data = (await client.post('/api/v1/model-registry', payload)).data as ModelCreateResponse;
  return unwrapItem<ModelRegistryItem>(data);
}

export async function getModel(modelId: string): Promise<ModelRegistryItem> {
  if (API_MODE === 'mock') {
    return {
      model_id: modelId,
      model_name: 'demo-model',
      disease_agent: 'capcop_agent',
      task_type: 'risk_assessment',
      modality_scope: ['ct'],
      owner_team: 'diagnostics',
      description: 'demo',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      versions: [],
    };
  }
  const data = (await client.get('/api/v1/model-registry/' + modelId)).data;
  return unwrapItem<ModelRegistryItem>(data);
}

export async function createModelVersion(modelId: string, payload: ModelVersionCreatePayload): Promise<ModelVersionItem> {
  if (API_MODE === 'mock') {
    return {
      version_id: 'version-demo-created',
      model_id: modelId,
      version_label: payload.version_label,
      approval_state: 'draft',
      contract_version: 'v1',
      artifact_ref: payload.artifact_ref,
      input_schema: payload.input_schema || {},
      output_schema: payload.output_schema || {},
      metrics: payload.metrics || {},
      runtime_constraints: payload.runtime_constraints || {},
      notes: payload.notes || null,
      approved_by: null,
      approved_at: null,
      promoted_by: null,
      promoted_at: null,
      archived_at: null,
      rollback_from_version_id: null,
      published_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  const data = (await client.post('/api/v1/model-registry/' + modelId + '/versions', payload)).data as ModelVersionResponse;
  return unwrapItem<ModelVersionItem>(data);
}

export async function approveModelVersion(versionId: string) {
  return (await client.post('/api/v1/model-versions/' + versionId + '/approve', {})).data as ModelVersionResponse;
}

export async function promoteModelVersion(versionId: string, targetState: string) {
  return (await client.post('/api/v1/model-versions/' + versionId + '/promote', { target_state: targetState })).data as ModelVersionResponse;
}

export async function rollbackModelVersion(versionId: string, targetVersionId: string) {
  return (await client.post('/api/v1/model-versions/' + versionId + '/rollback', { rollback_to_version_id: targetVersionId, target_version_id: targetVersionId })).data as ModelVersionResponse;
}

export async function getModelVersionEvaluations(versionId: string): Promise<ModelVersionEvaluationsResponse> {
  if (API_MODE === 'mock') {
    return {
      status: 'ok',
      route: '/api/v1/model-versions/' + versionId + '/evaluations',
      item: {
        version_id: versionId,
        overall_score: 0.82,
        metrics: { auc: 0.82, f1: 0.71 },
        notes: 'demo evaluation summary',
      },
    };
  }
  const data = (await client.get('/api/v1/model-versions/' + versionId + '/evaluations')).data;
  return unwrapItem<ModelVersionEvaluationsResponse>(data);
}

export async function getTrace(traceId: string) {
  if (API_MODE === 'mock') return { trace_id: traceId, status: 'completed' };
  const url = '/api/v1/traces/' + traceId;
  return (await client.get(url, withTraceId(traceId))).data;
}

export async function getTraceEvents(traceId: string) {
  if (API_MODE === 'mock') return [];
  const url = '/api/v1/traces/' + traceId + '/events';
  const data = (await client.get(url, withTraceId(traceId))).data;
  return unwrapList<TraceEventItem>(data);
}

export async function createInferenceTask(caseId: string, payload: InferenceTaskPayload, traceId?: string): Promise<InferenceTaskResponse> {
  const url = '/api/v1/cases/' + caseId + '/inference-tasks';
  if (API_MODE === 'mock') {
    return {
      trace_id: traceId || 'trace-demo',
      task_id: 'task-demo',
      model_invocation_id: 'invoke-demo',
      model_version_id: 'capcop_stub_v1',
      confidence: 0.66,
      uncertainty: { mode: 'stub' },
      limitations: ['demo-only'],
      recommendation: { evidence_refs: ['stub://ct/1'] },
      model_service: { mode: 'mock' }
    };
  }
  return (await client.post(url, payload, withTraceId(traceId))).data;
}


export type ModelInputFeatureRequirement = {
  feature_order: number;
  source_clinical_field: string;
  model_feature_name: string;
  feature_type?: string | null;
  required?: boolean;
  optional?: boolean;
  defaultable?: boolean;
  default_strategy?: string | null;
  missing_value_policy?: string | null;
  unit?: string | null;
  value_range?: Record<string, unknown> | null;
  enum_mapping?: Record<string, unknown> | null;
  notes?: string | null;
};

export type ModelInputSchemaResponse = {
  model_version_id: string;
  model_id: string;
  model_name?: string | null;
  version_label?: string | null;
  model_input_schema_id: string;
  model_input_schema_key: string;
  model_input_schema_name?: string | null;
  schema_version?: string | null;
  disease_task?: string | null;
  disease_task_feature_set_id?: string | null;
  disease_task_feature_set_key?: string | null;
  disease_task_feature_set_name?: string | null;
  supported_disease_tasks?: string[];
  supported_modalities?: string[];
  lifecycle_status?: string | null;
  model_family?: string | null;
  preprocess_artifact_ref?: string | null;
  feature_count?: number;
  feature_requirements: ModelInputFeatureRequirement[];
};

export type ModelInputFeatureRequirementsResponse = {
  status?: string;
  route?: string;
  model_version_id: string;
  model_input_schema_id: string;
  model_input_schema_key: string;
  disease_task_feature_set_id?: string | null;
  disease_task_feature_set_key?: string | null;
  feature_count?: number;
  required_count?: number;
  optional_count?: number;
  defaultable_count?: number;
  feature_requirements: ModelInputFeatureRequirement[];
};

export type ModelInputPreviewPayload = {
  disease_task: string;
  model_version_id: string;
  model_input?: Record<string, unknown>;
  provided_features?: Record<string, unknown>;
};

export type ModelInputPreviewItem = {
  model_version_id: string;
  model_input_schema_id?: string | null;
  model_input_schema_key?: string | null;
  disease_task_feature_set_id?: string | null;
  disease_task_feature_set_key?: string | null;
  disease_task?: string | null;
  mapped_features?: Record<string, unknown> | null;
  provided_features?: string[] | Record<string, unknown> | null;
  missing_features?: string[];
  missing_required_features?: string[];
  missing_required_details?: Array<{
    model_feature_name?: string;
    source_clinical_field?: string;
    why_required?: string;
    default_strategy?: string | null;
    missing_value_policy?: string | null;
    suggested_doctor_question?: string | null;
  }>;
  defaultable_features?: string[];
  suggested_doctor_questions?: string[];
  current_assessment_status?: string | null;
  insufficient_data_for_assessment?: boolean | null;
};

export type ModelInputPreviewResponse = {
  status?: string;
  route?: string;
  item: ModelInputPreviewItem;
};

export type ModelSelectionCandidate = {
  model_version_id: string;
  model_id: string;
  model_name: string;
  version_label: string;
  model_input_schema_id?: string | null;
  model_input_schema_key?: string | null;
  lifecycle_status?: string | null;
  supported_modalities?: string[];
  feature_completeness?: number | null;
  missing_fields?: string[];
  missing_required_features?: string[];
  defaultable_features?: string[];
  suitability_reason?: string | null;
  current_assessment_status?: string | null;
  insufficient_data_for_assessment?: boolean | null;
  runtime_stub?: boolean | null;
};

export type ModelSelectionPreviewResponse = {
  status?: string;
  route?: string;
  disease_task?: string;
  selection_required?: boolean;
  selection_reason?: string | null;
  candidate_count?: number;
  selected_candidate?: ModelSelectionCandidate | null;
  validation?: Record<string, unknown> | null;
  candidates: ModelSelectionCandidate[];
};

export type ModelSelectionPayload = {
  disease_task: string;
  candidate_model_version_ids: string[];
};

export async function getModelInputSchema(modelVersionId: string): Promise<ModelInputSchemaResponse> {
  if (API_MODE === 'mock') {
    return {
      model_version_id: modelVersionId,
      model_id: 'model-demo',
      model_name: 'demo-model',
      version_label: 'v0.1.0',
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      model_input_schema_key: 'clinical_mlp_cap_cop_input_schema_v1',
      model_input_schema_name: 'clinical_mlp_cap_cop_input_schema_v1',
      schema_version: 'v1',
      disease_task: 'cap_cop',
      disease_task_feature_set_id: 'cap_cop_clinical_feature_set_v1',
      disease_task_feature_set_key: 'cap_cop_clinical_feature_set_v1',
      disease_task_feature_set_name: 'CAP/COP Clinical Feature Set v1',
      supported_disease_tasks: ['cap_cop'],
      supported_modalities: ['clinical_table'],
      lifecycle_status: 'default',
      model_family: 'clinical_mlp',
      preprocess_artifact_ref: 'metadata-only://demo',
      feature_count: 0,
      feature_requirements: [],
    };
  }
  const data = (await client.get('/api/v1/model-input-schemas/' + modelVersionId)).data;
  return data as ModelInputSchemaResponse;
}

export async function getModelFeatureRequirements(modelVersionId: string): Promise<ModelInputFeatureRequirementsResponse> {
  if (API_MODE === 'mock') {
    return {
      status: 'ok',
      route: '/api/v1/model-input-schemas/' + modelVersionId + '/feature-requirements',
      model_version_id: modelVersionId,
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      model_input_schema_key: 'clinical_mlp_cap_cop_input_schema_v1',
      disease_task_feature_set_id: 'cap_cop_clinical_feature_set_v1',
      disease_task_feature_set_key: 'cap_cop_clinical_feature_set_v1',
      feature_count: 0,
      required_count: 0,
      optional_count: 0,
      defaultable_count: 0,
      feature_requirements: [],
    };
  }
  const data = (await client.get('/api/v1/model-input-schemas/' + modelVersionId + '/feature-requirements')).data;
  return data as ModelInputFeatureRequirementsResponse;
}

export async function previewCaseModelInput(caseId: string, payload: ModelInputPreviewPayload): Promise<ModelInputPreviewItem> {
  if (API_MODE === 'mock') {
    return {
      model_version_id: payload.model_version_id,
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      model_input_schema_key: 'clinical_mlp_cap_cop_input_schema_v1',
      disease_task_feature_set_id: 'cap_cop_clinical_feature_set_v1',
      disease_task_feature_set_key: 'cap_cop_clinical_feature_set_v1',
      disease_task: payload.disease_task,
      mapped_features: {},
      missing_features: ['Age'],
      missing_required_features: ['Age'],
      missing_required_details: [{ model_feature_name: 'Age', source_clinical_field: 'Age', why_required: 'demo', default_strategy: null, missing_value_policy: 'consult_doctor_first', suggested_doctor_question: 'Please provide Age.' }],
      defaultable_features: [],
      suggested_doctor_questions: ['Please provide Age.'],
      current_assessment_status: 'awaiting_doctor_input',
      insufficient_data_for_assessment: true,
    };
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/model-input-preview', payload)).data;
  return unwrapItem<ModelInputPreviewItem>(data);
}

export async function validateCaseModelInput(caseId: string, payload: ModelInputPreviewPayload): Promise<ModelInputPreviewItem> {
  if (API_MODE === 'mock') {
    return {
      model_version_id: payload.model_version_id,
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      model_input_schema_key: 'clinical_mlp_cap_cop_input_schema_v1',
      disease_task_feature_set_id: 'cap_cop_clinical_feature_set_v1',
      disease_task_feature_set_key: 'cap_cop_clinical_feature_set_v1',
      disease_task: payload.disease_task,
      mapped_features: {},
      missing_features: ['Age'],
      missing_required_features: ['Age'],
      missing_required_details: [{ model_feature_name: 'Age', source_clinical_field: 'Age', why_required: 'demo', default_strategy: null, missing_value_policy: 'consult_doctor_first', suggested_doctor_question: 'Please provide Age.' }],
      defaultable_features: [],
      suggested_doctor_questions: ['Please provide Age.'],
      current_assessment_status: 'awaiting_doctor_input',
      insufficient_data_for_assessment: true,
    };
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/model-input-validation', payload)).data;
  return unwrapItem<ModelInputPreviewItem>(data);
}

export async function previewModelSelection(caseId: string, payload: ModelSelectionPayload): Promise<ModelSelectionPreviewResponse> {
  if (API_MODE === 'mock') {
    return {
      status: 'ok',
      route: '/api/v1/cases/' + caseId + '/model-selection-preview',
      disease_task: payload.disease_task,
      selection_required: payload.candidate_model_version_ids.length > 1,
      selection_reason: payload.candidate_model_version_ids.length > 1 ? 'multiple_candidates' : 'single_candidate',
      candidate_count: payload.candidate_model_version_ids.length,
      selected_candidate: null,
      validation: null,
      candidates: [],
    };
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/model-selection-preview', payload)).data;
  return data as ModelSelectionPreviewResponse;
}


export type ShadowInferenceRunOutputItem = {
  id: string;
  output_id: string;
  shadow_run_id: string;
  trace_id: string;
  case_id: string;
  model_version_id: string;
  prediction_raw_json?: unknown | null;
  prediction_probability_json?: Record<string, unknown> | null;
  candidate_label?: string | null;
  confidence_json?: Record<string, unknown> | null;
  uncertainty_json?: Record<string, unknown> | null;
  limitations_json?: Record<string, unknown> | null;
  input_quality_flags_json?: Record<string, unknown> | null;
  created_at?: string | null;
};

export type ShadowInferenceRunItem = {
  id: string;
  shadow_run_id: string;
  trace_id: string;
  case_id: string;
  patient_id?: string | null;
  model_version_id: string;
  artifact_hash?: string | null;
  adapter_code?: string | null;
  model_input_schema_id?: string | null;
  input_snapshot_id?: string | null;
  status?: string | null;
  runtime_env_json?: Record<string, unknown> | null;
  runtime_stub?: boolean | null;
  not_for_diagnosis?: boolean | null;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  error_code?: string | null;
  error_detail_json?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
  outputs?: ShadowInferenceRunOutputItem[];
};

export type ShadowInferenceRunListResponse = {
  items: ShadowInferenceRunItem[];
  total: number;
};

export type ShadowInferenceRunOutputsResponse = {
  items: ShadowInferenceRunOutputItem[];
  total: number;
};

export type ShadowInferenceRunResponse = {
  status?: string;
  route?: string;
  item: ShadowInferenceRunItem;
};

export async function getShadowInferenceRun(shadowRunId: string): Promise<ShadowInferenceRunItem> {
  if (API_MODE === 'mock') {
    return {
      id: 'shadow-demo-id',
      shadow_run_id: shadowRunId,
      trace_id: 'trace-demo',
      case_id: 'case-001',
      patient_id: 'patient-001',
      model_version_id: 'capcop_stub_v1',
      artifact_hash: 'shadow-demo-hash-001',
      adapter_code: 'capcop_agent',
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      input_snapshot_id: 'snapshot-demo',
      status: 'shadow_success',
      runtime_env_json: { env: 'dev', shadow: true },
      runtime_stub: true,
      not_for_diagnosis: true,
      started_at: new Date().toISOString(),
      completed_at: null,
      duration_ms: null,
      error_code: null,
      error_detail_json: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outputs: [],
    };
  }
  const data = (await client.get('/api/v1/shadow-inference-runs/' + shadowRunId)).data;
  return unwrapItem<ShadowInferenceRunItem>(data);
}

export async function listShadowRunsByCase(caseId: string): Promise<ShadowInferenceRunListResponse> {
  if (API_MODE === 'mock') {
    const item: ShadowInferenceRunItem = {
      id: 'shadow-demo-id',
      shadow_run_id: 'shadow_dbf2a913fa5c4266',
      trace_id: 'trace-demo',
      case_id: caseId,
      patient_id: 'patient-001',
      model_version_id: 'capcop_stub_v1',
      artifact_hash: 'shadow-demo-hash-001',
      adapter_code: 'capcop_agent',
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      input_snapshot_id: 'snapshot-demo',
      status: 'shadow_success',
      runtime_env_json: { env: 'dev', shadow: true },
      runtime_stub: true,
      not_for_diagnosis: true,
      started_at: new Date().toISOString(),
      completed_at: null,
      duration_ms: 120,
      error_code: null,
      error_detail_json: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return { items: [item], total: 1 };
  }
  const data = (await client.get('/api/v1/cases/' + caseId + '/shadow-inference-runs')).data;
  const items = unwrapList<ShadowInferenceRunItem>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { items, total };
}

export async function listShadowRunsByTrace(traceId: string): Promise<ShadowInferenceRunListResponse> {
  if (API_MODE === 'mock') {
    const item: ShadowInferenceRunItem = {
      id: 'shadow-demo-id',
      shadow_run_id: 'shadow_dbf2a913fa5c4266',
      trace_id: traceId,
      case_id: 'case-001',
      patient_id: 'patient-001',
      model_version_id: 'capcop_stub_v1',
      artifact_hash: 'shadow-demo-hash-001',
      adapter_code: 'capcop_agent',
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      input_snapshot_id: 'snapshot-demo',
      status: 'shadow_success',
      runtime_env_json: { env: 'dev', shadow: true },
      runtime_stub: true,
      not_for_diagnosis: true,
      started_at: new Date().toISOString(),
      completed_at: null,
      duration_ms: 120,
      error_code: null,
      error_detail_json: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return { items: [item], total: 1 };
  }
  const data = (await client.get('/api/v1/traces/' + traceId + '/shadow-inference-runs')).data;
  const items = unwrapList<ShadowInferenceRunItem>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { items, total };
}

export async function getShadowRunOutputs(shadowRunId: string): Promise<ShadowInferenceRunOutputsResponse> {
  if (API_MODE === 'mock') {
    return {
      items: [
        {
          id: 'shadow-output-demo-1',
          output_id: 'out_64b0a4b9c5a64653',
          shadow_run_id: shadowRunId,
          trace_id: 'trace-demo',
          case_id: 'case-001',
          model_version_id: 'capcop_stub_v1',
          prediction_raw_json: { label: 'shadow_positive' },
          prediction_probability_json: { shadow_positive: 0.82 },
          candidate_label: 'shadow_positive',
          confidence_json: { value: 0.82 },
          uncertainty_json: { value: 0.18 },
          limitations_json: { notes: ['metadata_only', 'not_for_diagnosis'] },
          input_quality_flags_json: { missing_required_features: [] },
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
    };
  }
  const data = (await client.get('/api/v1/shadow-inference-runs/' + shadowRunId + '/outputs')).data;
  const items = unwrapList<ShadowInferenceRunOutputItem>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { items, total };
}








