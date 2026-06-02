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
    { case_id: 'case-002', patient_id: 'patient-002', disease_task: 'COP', status: 'awaiting_input', trace_id: 'trace-demo-2' }
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
      updated_at: '2026-06-02T00:00:00Z'
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
      updated_at: '2026-06-02T00:00:00Z'
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
      updated_at: '2026-06-02T00:00:00Z'
    }
  ],
  recommendations: [
    { recommendation_id: 'rec-001', title: '示例推荐结果', risk_score: 0.78, trace_id: 'trace-demo' }
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
      updated_at: '2026-06-02T00:00:00Z'
    }
  ]
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
