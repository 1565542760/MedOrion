import axios, { type AxiosRequestConfig } from 'axios';
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

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
};

export type CaseItem = {
  case_id: string;
  patient_id: string;
  case_no?: string | null;
  disease_task?: string | null;
  status?: string | null;
  trace_id?: string | null;
  chief_complaint?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PatientCreatePayload = {
  external_patient_id?: string | null;
  display_name?: string | null;
  name?: string | null;
  sex?: string | null;
  birth_date?: string | null;
  consent_status?: string | null;
};

export type CaseCreatePayload = {
  patient_id: string;
  case_no?: string | null;
  disease_task?: string | null;
  status?: string | null;
  chief_complaint?: string | null;
};

export type CaseImagingInputCreatePayload = {
  patient_id?: string | null;
  trace_id?: string | null;
  modality?: string | null;
  source_type?: string | null;
  storage_uri?: string | null;
  deidentified?: boolean | null;
  not_for_diagnosis?: boolean | null;
  provenance_json?: Record<string, unknown> | null;
  quality_flags_json?: Record<string, unknown> | null;
};

export type PatientItem = {
  patient_id: string;
  external_patient_id?: string | null;
  display_name?: string | null;
  sex?: string | null;
  birth_date?: string | null;
  consent_status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CaseImagingInputItem = {
  input_asset_id: string;
  case_id?: string | null;
  patient_id?: string | null;
  trace_id?: string | null;
  modality?: string | null;
  source_type?: string | null;
  storage_uri?: string | null;
  deidentified?: boolean | null;
  not_for_diagnosis?: boolean | null;
  provenance_json?: Record<string, unknown> | null;
  quality_flags_json?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type DicomSeriesRegisterResponse = CaseImagingInputItem & {
  status?: string | null;
  route?: string | null;
  source_format?: string | null;
  preprocessed_format?: string | null;
  preprocessing_status?: string | null;
  preprocessing_error_code?: string | null;
  preprocessing_error_message?: string | null;
  preprocessing_script?: string | null;
  conversion_tool?: string | null;
  bias_correction?: string | null;
  raw_output_file?: string | null;
  model_input_file?: string | null;
  label_file?: string | null;
  message?: string | null;
};

export type ImagingPreprocessingStatusResponse = DicomSeriesRegisterResponse;

export type ImagingPreprocessResponse = ImagingPreprocessingStatusResponse & {
  error_code?: string | null;
};

export type CaseImagingInputListResponse = {
  status?: string | null;
  route?: string | null;
  total: number;
  limit: number;
  offset: number;
  items: CaseImagingInputItem[];
};

export type DicomSeriesRegisterPayload = {
  series_label: string;
  source_type: string;
  dicom_series_ref: string;
  storage_uri?: string;
  deidentified?: boolean;
  not_for_diagnosis?: boolean;
  provenance_json?: Record<string, unknown>;
  quality_flags_json?: Record<string, unknown>;
};

export type DicomSeriesUploadPayload = {
  patient_id: string;
  trace_id: string;
  files: File[];
  modality?: string;
  source_type?: string;
  deidentified?: boolean;
  not_for_diagnosis?: boolean;
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

export const apiConfig = { mode: API_MODE, baseURL: API_BASE_URL };

const mock = {
  cases: [
    { case_id: 'case-001', patient_id: 'patient-001', disease_task: 'cap_cop', status: 'in_review', trace_id: 'trace-demo', case_no: 'MO-CASE-001' },
    { case_id: 'case-002', patient_id: 'patient-002', disease_task: 'cap_cop', status: 'awaiting_input', trace_id: 'trace-demo-2', case_no: 'MO-CASE-002' },
  ],
  imagingInputs: [
    {
      input_asset_id: 'img-demo-001',
      case_id: 'case-001',
      patient_id: 'patient-001',
      trace_id: 'trace-demo',
      modality: 'CT',
      source_type: 'demo',
      storage_uri: 'managed://coursework-demo/case-001/ct-series-01',
      deidentified: true,
      not_for_diagnosis: true,
      provenance_json: { origin: 'coursework-demo', capture_mode: 'manual-registration', source_case_link: 'case-001' },
      quality_flags_json: { artifact_free: true, slice_count_ok: true, orientation_ok: true },
      created_at: '2026-06-08T00:00:00Z',
      updated_at: '2026-06-08T00:00:00Z',
    },
  ] as CaseImagingInputItem[],
  missingQueries: [
    {
      query_id: 'query-demo-pending',
      case_id: 'case-001',
      patient_id: 'patient-001',
      field_name: 'wbc',
      field_label: '白细胞',
      modality: 'lab',
      reason: 'demo',
      question_text: '请补充白细胞值。',
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
      question_text: '请补充CRP值。',
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
      question_text: '请补充降钙素原。',
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
    { recommendation_id: 'rec-001', title: 'Demo recommendation', risk_score: 0.78, trace_id: 'trace-demo' },
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
      summary: 'Demo quality review',
      related_feedback_id: 'feedback-demo-001',
      opened_by: 'dev_doctor',
      created_at: '2026-06-02T00:00:00Z',
      updated_at: '2026-06-02T00:00:00Z',
    },
  ],
};

client.interceptors.request.use((config) => {
  config.headers.set('x-request-id', uuidv4());
  const token = getAccessToken();
  if (token) {
    config.headers.set('Authorization', 'Bearer ' + token);
  }
  return config;
});

function isAuthRoute(url?: string | null) {
  return !!url && (url.includes('/api/v1/auth/login') || url.includes('/api/v1/auth/refresh') || url.includes('/api/v1/auth/logout'));
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;
    const config = error?.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (status === 401 && config && !config._retry && !isAuthRoute(config.url)) {
      config._retry = true;
      try {
        await refreshToken();
        const token = getAccessToken();
        if (token) {
          const headers = config.headers as { set?: (name: string, value: string) => void } & Record<string, string>;
          if (headers && typeof headers.set === 'function') {
            headers.set('Authorization', 'Bearer ' + token);
          } else {
            config.headers = { ...(config.headers || {}), Authorization: 'Bearer ' + token } as AxiosRequestConfig['headers'];
          }
        }
        return client.request(config);
      } catch {
        clearAuthTokens();
      }
    }
    return Promise.reject(error);
  },
);

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

function describeApiErrorDetail(detail: unknown): string | null {
  if (!detail) return null;
  if (typeof detail === 'string') {
    const trimmed = detail.trim();
    return trimmed || null;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (!item || typeof item !== 'object') return null;
        const entry = item as { loc?: unknown[]; msg?: string; code?: string };
        const loc = Array.isArray(entry.loc) ? entry.loc.map((value) => String(value)).join('.') : '';
        const msg = entry.msg || entry.code || '';
        if (!loc && !msg) return null;
        return loc ? loc + ': ' + msg : msg;
      })
      .filter((value): value is string => !!value);
    return parts.length ? parts.join('；') : null;
  }
  if (typeof detail === 'object') {
    const entry = detail as { message?: string; code?: string; detail?: unknown };
    if (typeof entry.message === 'string' && entry.message.trim()) return entry.message.trim();
    if (typeof entry.code === 'string' && entry.code.trim()) return entry.code.trim();
    if ('detail' in entry) return describeApiErrorDetail(entry.detail);
  }
  return null;
}

export function extractErrorMessage(detail: string, fallback: string) {
  if (!detail) return fallback;
  try {
    const parsed = JSON.parse(detail) as { detail?: unknown; message?: string };
    return describeApiErrorDetail(parsed.detail) || parsed?.message || fallback;
  } catch {
    return detail || fallback;
  }
}

export function formatApiErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401) return '认证已过期，请重新登录后继续操作。';
    if (status === 403) return '当前账号无权执行此操作。';
    const detail = error.response?.data;
    if (typeof detail === 'string') return extractErrorMessage(detail, fallback);
    return describeApiErrorDetail(detail) || fallback;
  }
  if (error instanceof Error) {
    if (error.message.includes('401')) return '认证已过期，请重新登录后继续操作。';
    if (error.message.trim()) return error.message;
  }
  return fallback;
}

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
  if (API_MODE === 'mock') {
    const data: LoginResponse = { access_token: 'mock-access-token', refresh_token: 'mock-refresh-token', token_type: 'Bearer', expires_in: 3600 };
    saveAuthTokens(data.access_token, data.refresh_token);
    return data;
  }
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
  if (API_MODE === 'mock') {
    const user: CurrentUser = { user_id: 'user-dev-doctor', username: 'dev_doctor', display_name: 'Dev Doctor', role: 'doctor', is_active: true };
    saveCurrentUser(user);
    return user;
  }
  const data = (await client.get('/api/v1/auth/me')).data as CurrentUser;
  saveCurrentUser(data);
  return data;
}

export async function refreshToken(): Promise<LoginResponse> {
  const rt = getRefreshToken();
  if (!rt) {
    throw new Error('missing_refresh_token');
  }
  if (API_MODE === 'mock') {
    const data: LoginResponse = { access_token: 'mock-access-token', refresh_token: 'mock-refresh-token', token_type: 'Bearer', expires_in: 3600 };
    saveAuthTokens(data.access_token, data.refresh_token);
    return data;
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

export async function listPatients(): Promise<PatientItem[]> {
  if (API_MODE === 'mock') {
    return [
      { patient_id: 'patient-001', external_patient_id: 'P-001', display_name: 'Demo Patient 001', sex: 'male', birth_date: '1980-01-01', consent_status: 'unknown' },
      { patient_id: 'patient-002', external_patient_id: 'P-002', display_name: 'Demo Patient 002', sex: 'female', birth_date: '1982-02-02', consent_status: 'unknown' },
    ];
  }
  const data = (await client.get('/api/v1/patients')).data;
  return unwrapList<PatientItem>(data);
}

export async function createPatient(payload: PatientCreatePayload): Promise<PatientItem> {
  if (API_MODE === 'mock') {
    return {
      patient_id: 'patient-demo-created',
      external_patient_id: payload.external_patient_id || null,
      display_name: payload.display_name || payload.name || 'Demo Patient',
      sex: payload.sex || null,
      birth_date: payload.birth_date || null,
      consent_status: payload.consent_status || 'unknown',
    };
  }
  const data = (await client.post('/api/v1/patients', payload)).data;
  return unwrapItem<PatientItem>(data);
}

export async function listCases(traceId?: string): Promise<CaseItem[]> {
  if (API_MODE === 'mock') return mock.cases as CaseItem[];
  const data = (await client.get('/api/v1/cases', withTraceId(traceId))).data;
  return unwrapList<CaseItem>(data);
}

export async function createCase(payload: CaseCreatePayload): Promise<CaseItem> {
  if (API_MODE === 'mock') {
    return {
      case_id: 'case-demo-created',
      patient_id: payload.patient_id,
      case_no: payload.case_no || 'MO-CASE-DEMO',
      disease_task: payload.disease_task || 'cap_cop',
      status: payload.status || 'open',
      trace_id: 'trace-demo-created',
      chief_complaint: payload.chief_complaint || null,
    };
  }
  const data = (await client.post('/api/v1/cases', payload)).data;
  return unwrapItem<CaseItem>(data);
}

export async function createCaseImagingInput(caseId: string, payload: CaseImagingInputCreatePayload): Promise<CaseImagingInputItem> {
  if (API_MODE === 'mock') {
    const item: CaseImagingInputItem = {
      input_asset_id: 'img-demo-created',
      case_id: caseId,
      patient_id: payload.patient_id || 'patient-001',
      trace_id: payload.trace_id || 'trace-demo',
      modality: payload.modality,
      source_type: payload.source_type,
      storage_uri: payload.storage_uri,
      deidentified: payload.deidentified ?? true,
      not_for_diagnosis: payload.not_for_diagnosis ?? true,
      provenance_json: payload.provenance_json || {},
      quality_flags_json: payload.quality_flags_json || {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mock.imagingInputs = [item, ...mock.imagingInputs as CaseImagingInputItem[]];
    return item;
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/imaging-inputs', payload, withTraceId(payload.trace_id || undefined))).data;
  return unwrapItem<CaseImagingInputItem>(data);
}

export async function listCaseImagingInputs(caseId: string, limit: number = 20, offset: number = 0): Promise<CaseImagingInputListResponse> {
  if (API_MODE === 'mock') {
    const items = mock.imagingInputs.filter((item) => item.case_id === caseId);
    return { status: 'ok', route: '/api/v1/cases/' + caseId + '/imaging-inputs', total: items.length, limit, offset, items: items.slice(offset, offset + limit) };
  }
  const data = (await client.get('/api/v1/cases/' + caseId + '/imaging-inputs', { params: { limit, offset } })).data;
  const items = unwrapList<CaseImagingInputItem>(data);
  const total = typeof data?.total === 'number' ? data.total : items.length;
  return { status: data?.status, route: data?.route, total, limit, offset, items };
}

export async function getCaseImagingInput(inputAssetId: string): Promise<CaseImagingInputItem> {
  if (API_MODE === 'mock') {
    return mock.imagingInputs.find((item) => item.input_asset_id === inputAssetId) || {
      input_asset_id: inputAssetId,
      case_id: 'case-001',
      patient_id: 'patient-001',
      trace_id: 'trace-demo',
      modality: 'CT',
      source_type: 'demo',
      storage_uri: 'managed://coursework-demo/case-001/ct-series-01',
      deidentified: true,
      not_for_diagnosis: true,
      provenance_json: { origin: 'coursework-demo' },
      quality_flags_json: { artifact_free: true },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  const data = (await client.get('/api/v1/imaging-inputs/' + inputAssetId)).data;
  return unwrapItem<CaseImagingInputItem>(data);
}

export async function registerDicomSeries(caseId: string, payload: DicomSeriesRegisterPayload): Promise<DicomSeriesRegisterResponse> {
  if (API_MODE === 'mock') {
    const item = await createCaseImagingInput(caseId, {
      patient_id: null,
      trace_id: null,
      modality: 'CT',
      source_type: payload.source_type,
      storage_uri: payload.storage_uri || payload.dicom_series_ref,
      deidentified: payload.deidentified ?? true,
      not_for_diagnosis: payload.not_for_diagnosis ?? true,
      provenance_json: payload.provenance_json || { series_label: payload.series_label, dicom_series_ref: payload.dicom_series_ref },
      quality_flags_json: payload.quality_flags_json || {},
    });
    return {
      ...item,
      source_format: 'dicom_series',
      preprocessed_format: 'nifti_nii_gz',
      preprocessing_status: 'pending',
    };
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/imaging-inputs/dicom-series', payload)).data;
  return unwrapItem<DicomSeriesRegisterResponse>(data);
}

export async function uploadDicomSeriesFiles(caseId: string, payload: DicomSeriesUploadPayload): Promise<ImagingPreprocessingStatusResponse> {
  if (API_MODE === 'mock') {
    const manifest = payload.files.map((file) => ({ filename: file.name, size_bytes: file.size, content_type: file.type || null }));
    return {
      status: 'ok',
      route: '/api/v1/cases/' + caseId + '/imaging-inputs/dicom-series/upload',
      input_asset_id: 'img-demo-upload-' + Math.random().toString(36).slice(2),
      case_id: caseId,
      patient_id: payload.patient_id,
      trace_id: payload.trace_id,
      modality: payload.modality || 'CT',
      source_type: payload.source_type || 'real_deidentified',
      storage_uri: 'managed://coursework-upload/' + caseId + '/' + Date.now(),
      deidentified: payload.deidentified ?? true,
      not_for_diagnosis: payload.not_for_diagnosis ?? true,
      source_format: 'dicom_series',
      preprocessed_format: 'nifti_nii_gz',
      preprocessing_script: 'dcmtonii_N4.py',
      conversion_tool: 'dcm2niix',
      bias_correction: 'N4BiasFieldCorrection',
      raw_output_file: 'raw_image.nii.gz',
      model_input_file: 'image.nii.gz',
      label_file: 'label.nii.gz',
      preprocessing_status: 'pending',
      provenance_json: { upload_state: 'uploaded_to_controlled_storage', upload_file_count: payload.files.length, upload_manifest: manifest },
      quality_flags_json: { upload_state: 'uploaded_to_controlled_storage', upload_file_count: payload.files.length, upload_manifest: manifest },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  const formData = new FormData();
  payload.files.forEach((file) => formData.append('files', file, file.name));
  formData.append('patient_id', payload.patient_id);
  formData.append('trace_id', payload.trace_id);
  formData.append('modality', payload.modality || 'CT');
  formData.append('source_type', payload.source_type || 'real_deidentified');
  formData.append('deidentified', String(payload.deidentified ?? true));
  formData.append('not_for_diagnosis', String(payload.not_for_diagnosis ?? true));
  const accessToken = getAccessToken();
  const response = await fetch(API_BASE_URL + '/api/v1/cases/' + caseId + '/imaging-inputs/dicom-series/upload', {
    method: 'POST',
    headers: {
      'x-request-id': uuidv4(),
      ...(payload.trace_id ? { 'x-trace-id': payload.trace_id } : {}),
      ...(accessToken ? { Authorization: 'Bearer ' + accessToken } : {}),
    },
    body: formData,
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(extractErrorMessage(detail, 'DICOM 文件上传失败，请稍后重试。'));
  }
  const bodyText = await response.text();
  const data = bodyText ? JSON.parse(bodyText) : null;
  return unwrapItem<ImagingPreprocessingStatusResponse>(data);
}

export async function getImagingPreprocessingStatus(inputAssetId: string): Promise<ImagingPreprocessingStatusResponse> {
  if (API_MODE === 'mock') {
    return {
      status: 'ok',
      route: '/api/v1/imaging-inputs/' + inputAssetId + '/preprocessing-status',
      input_asset_id: inputAssetId,
      source_format: 'dicom_series',
      preprocessed_format: 'nifti_nii_gz',
      preprocessing_script: 'dcmtonii_N4.py',
      conversion_tool: 'dcm2niix',
      bias_correction: 'N4BiasFieldCorrection',
      raw_output_file: 'raw_image.nii.gz',
      model_input_file: 'image.nii.gz',
      label_file: 'label.nii.gz',
      preprocessing_status: 'not_implemented',
      provenance_json: {},
      quality_flags_json: {},
      message: 'preprocessing_not_implemented',
    };
  }
  const data = (await client.get('/api/v1/imaging-inputs/' + inputAssetId + '/preprocessing-status')).data;
  return unwrapItem<ImagingPreprocessingStatusResponse>(data);
}


export type CapCopShadowWorkflowBranchReadiness = {
  status: string;
  can_run: boolean;
  disabled_reasons: string[];
  required_inputs: string[];
  detected_inputs: string[];
  next_action?: string | null;
};

export type CapCopShadowWorkflowBranchPlan = CapCopShadowWorkflowBranchReadiness & {
  branch?: string | null;
  planned_status?: string | null;
  skipped_reason?: string | null;
  limitations?: unknown;
  shadow_run_id?: string | null;
  output_id?: string | null;
  candidate_label?: string | null;
  prediction_probability_json?: Record<string, unknown> | null;
  confidence_json?: Record<string, unknown> | null;
  uncertainty_json?: Record<string, unknown> | null;
  note?: string | null;
};

export type CapCopShadowWorkflowReadinessResponse = {
  status?: string | null;
  route?: string | null;
  overall_status?: string | null;
  branches: {
    clinical_mlp: CapCopShadowWorkflowBranchReadiness;
    imaging_resnet18: CapCopShadowWorkflowBranchReadiness;
    multimodal_resnet18: CapCopShadowWorkflowBranchReadiness;
  };
};

export type CapCopShadowWorkflowResponse = {
  status?: string | null;
  route?: string | null;
  mode?: string | null;
  overall_status?: string | null;
  execution_plan?: {
    overall_status?: string | null;
    branches: {
      clinical_mlp: CapCopShadowWorkflowBranchPlan;
      imaging_resnet18: CapCopShadowWorkflowBranchPlan;
      multimodal_resnet18: CapCopShadowWorkflowBranchPlan;
    };
    limitations?: string[];
  };
  branches: {
    clinical_mlp: CapCopShadowWorkflowBranchPlan;
    imaging_resnet18: CapCopShadowWorkflowBranchPlan;
    multimodal_resnet18: CapCopShadowWorkflowBranchPlan;
  };
  plan?: {
    overall_status?: string | null;
    branches: {
      clinical_mlp: CapCopShadowWorkflowBranchPlan;
      imaging_resnet18: CapCopShadowWorkflowBranchPlan;
      multimodal_resnet18: CapCopShadowWorkflowBranchPlan;
    };
    limitations?: string[];
  };
  result?: {
    branches: {
      clinical_mlp: CapCopShadowWorkflowBranchPlan;
      imaging_resnet18: CapCopShadowWorkflowBranchPlan;
      multimodal_resnet18: CapCopShadowWorkflowBranchPlan;
    };
  };
};

export async function requestImagingPreprocess(inputAssetId: string): Promise<ImagingPreprocessResponse> {
  if (API_MODE === 'mock') {
    return {
      status: 'not_implemented',
      route: '/api/v1/imaging-inputs/' + inputAssetId + '/preprocess',
      input_asset_id: inputAssetId,
      source_format: 'dicom_series',
      preprocessed_format: 'nifti_nii_gz',
      preprocessing_script: 'dcmtonii_N4.py',
      conversion_tool: 'dcm2niix',
      bias_correction: 'N4BiasFieldCorrection',
      raw_output_file: 'raw_image.nii.gz',
      model_input_file: 'image.nii.gz',
      label_file: 'label.nii.gz',
      preprocessing_status: 'not_implemented',
      provenance_json: {},
      quality_flags_json: {},
      message: 'preprocessing_not_implemented',
      error_code: 'preprocessing_not_implemented',
    };
  }

  const response = await client.post(
    '/api/v1/imaging-inputs/' + inputAssetId + '/preprocess',
    {
      dry_run: true,
      execute: false,
      execution_mode: 'plan_only',
      allow_real_preprocessing: false,
    },
    { timeout: 0 },
  );

  return response.data as ImagingPreprocessResponse;
}

export async function getCapCopShadowWorkflowReadiness(caseId: string): Promise<CapCopShadowWorkflowReadinessResponse> {
  if (API_MODE === 'mock') {
    const ready = caseId === 'case-001';
    const branchReady: CapCopShadowWorkflowBranchReadiness = {
      status: 'ready',
      can_run: true,
      disabled_reasons: [],
      required_inputs: ['clinical artifact-order snapshot', '需要预处理后的 image.nii.gz'],
      detected_inputs: ['ready_for_inference snapshot', 'NIfTI / synthetic imaging input'],
      next_action: '进入病例工作台的输入数据区域',
    };
    return {
      status: ready ? 'ready_all' : 'blocked',
      route: '/api/v1/cases/' + caseId + '/cap-cop-shadow/workflow-readiness',
      overall_status: ready ? 'ready_all' : 'blocked',
      branches: ready
        ? {
            clinical_mlp: { ...branchReady, detected_inputs: ['ready_for_inference snapshot', '36-feature artifact-order snapshot'] },
            imaging_resnet18: { ...branchReady, detected_inputs: ['preprocessed image.nii.gz', 'preprocessing_status=completed'] },
            multimodal_resnet18: { ...branchReady, detected_inputs: ['clinical + imaging both ready'] },
          }
        : {
            clinical_mlp: {
              status: 'blocked',
              can_run: false,
              disabled_reasons: ['临床 36 特征尚未完成 artifact-order 映射'],
              required_inputs: ['36-feature artifact-order snapshot'],
              detected_inputs: [],
              next_action: '进入 /cases/' + caseId + '/model-input',
            },
            imaging_resnet18: {
              status: 'blocked',
              can_run: false,
              disabled_reasons: ['影像输入尚未完成预处理'],
              required_inputs: ['image.nii.gz'],
              detected_inputs: [],
              next_action: '进入 /cases/' + caseId + '/imaging-inputs',
            },
            multimodal_resnet18: {
              status: 'blocked',
              can_run: false,
              disabled_reasons: ['multimodal 需要同时具备临床和影像输入'],
              required_inputs: ['clinical snapshot', 'image.nii.gz'],
              detected_inputs: [],
              next_action: '先补齐临床和影像输入',
            },
          },
    };
  }
  const data = (await client.get('/api/v1/cases/' + caseId + '/cap-cop-shadow/workflow-readiness')).data;
  return data as CapCopShadowWorkflowReadinessResponse;
}

function buildWorkflowPlanBranch(key: string, branch: CapCopShadowWorkflowBranchReadiness | CapCopShadowWorkflowBranchPlan | null | undefined, mode: 'preview' | 'execute') {
  const canRun = !!branch?.can_run;
  const disabledReasons = branch?.disabled_reasons || [];
  const detectedInputs = branch?.detected_inputs || [];
  const requiredInputs = branch?.required_inputs || [];
  const status = branch?.status || (canRun ? (mode === 'preview' ? 'planned' : 'executed') : 'skipped');
  const reason = (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.skipped_reason || disabledReasons[0] || (canRun ? null : 'branch blocked');
  return {
    branch: key,
    status,
    can_run: canRun,
    disabled_reasons: disabledReasons,
    required_inputs: requiredInputs,
    detected_inputs: detectedInputs,
    next_action: branch?.next_action || null,
    limitations: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.limitations || disabledReasons,
    skipped_reason: reason || null,
    shadow_run_id: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.shadow_run_id || null,
    output_id: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.output_id || null,
    candidate_label: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.candidate_label || null,
    prediction_probability_json: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.prediction_probability_json || null,
    confidence_json: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.confidence_json ?? null,
    uncertainty_json: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.uncertainty_json ?? null,
    note: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.note || null,
    planned_status: (branch as CapCopShadowWorkflowBranchPlan | null | undefined)?.planned_status || null,
  };
}

function buildWorkflowPlanResponse(caseId: string, readiness: CapCopShadowWorkflowReadinessResponse, mode: 'preview' | 'execute'): CapCopShadowWorkflowResponse {
  const branches = readiness.branches || {};
  const previewBranches = {
    clinical_mlp: buildWorkflowPlanBranch('clinical_mlp', branches.clinical_mlp, mode),
    imaging_resnet18: buildWorkflowPlanBranch('imaging_resnet18', branches.imaging_resnet18, mode),
    multimodal_resnet18: buildWorkflowPlanBranch('multimodal_resnet18', branches.multimodal_resnet18, mode),
  };
  return {
    status: 'ok',
    route: '/api/v1/cases/' + caseId + '/cap-cop-shadow/workflow',
    mode,
    overall_status: readiness.overall_status || null,
    execution_plan: {
      overall_status: readiness.overall_status || null,
      branches: previewBranches,
      limitations: [],
    },
    branches: previewBranches,
    plan: {
      overall_status: readiness.overall_status || null,
      branches: previewBranches,
      limitations: [],
    },
    result: {
      branches: previewBranches,
    },
  };
}

export async function previewCapCopShadowWorkflow(caseId: string, payload: Record<string, unknown> = {}): Promise<CapCopShadowWorkflowResponse> {
  if (API_MODE === 'mock') {
    const readiness = await getCapCopShadowWorkflowReadiness(caseId);
    return buildWorkflowPlanResponse(caseId, readiness, 'preview');
  }
  const accessToken = getAccessToken();
  const response = await fetch(API_BASE_URL + '/api/v1/cases/' + caseId + '/cap-cop-shadow/workflow', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-request-id': uuidv4(),
      ...(accessToken ? { Authorization: 'Bearer ' + accessToken } : {})
    },
    body: JSON.stringify({ ...payload, mode: 'preview' }),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(detail || 'preview_cap_cop_shadow_workflow_failed');
  }
  const bodyText = await response.text();
  return JSON.parse(bodyText) as CapCopShadowWorkflowResponse;
}

export async function executeCapCopShadowWorkflow(caseId: string, payload: Record<string, unknown>): Promise<CapCopShadowWorkflowResponse> {
  if (API_MODE === 'mock') {
    const readiness = await getCapCopShadowWorkflowReadiness(caseId);
    return buildWorkflowPlanResponse(caseId, readiness, 'execute');
  }
  const accessToken = getAccessToken();
  const response = await fetch(API_BASE_URL + '/api/v1/cases/' + caseId + '/cap-cop-shadow/workflow', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-request-id': uuidv4(),
      ...(accessToken ? { Authorization: 'Bearer ' + accessToken } : {})
    },
    body: JSON.stringify({ ...payload, mode: 'execute' }),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(detail || 'execute_cap_cop_shadow_workflow_failed');
  }
  const bodyText = await response.text();
  return JSON.parse(bodyText) as CapCopShadowWorkflowResponse;
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

export type ModelInputSnapshotCreatePayload = {
  trace_id: string;
  model_version_id: string;
  model_input_schema_id: string;
  disease_task_feature_set_id: string;
  preprocess_artifact_ref?: string | null;
  mapped_features: Record<string, unknown>;
  missing_features: unknown[];
  defaulted_features: unknown[];
  doctor_provided_features: unknown[];
  source_refs: unknown[];
  validation_status: 'ready_for_inference' | 'insufficient_data_for_assessment' | 'missing_required_features' | 'default_applied' | 'doctor_confirmation_required' | 'validation_failed';
  current_assessment_status: 'ready_for_inference' | 'insufficient_data_for_assessment' | 'missing_required_features' | 'default_applied' | 'doctor_confirmation_required' | 'validation_failed';
  insufficient_data_for_assessment: boolean;
  runtime_stub: true;
  not_for_diagnosis: true;
};

export type ModelInputSnapshotSummaryItem = {
  id: string;
  input_snapshot_id: string;
  case_id: string;
  patient_id: string;
  trace_id: string;
  model_version_id: string;
  model_input_schema_id: string;
  disease_task_feature_set_id: string;
  validation_status: string;
  current_assessment_status: string;
  insufficient_data_for_assessment?: boolean | null;
  runtime_stub?: boolean | null;
  not_for_diagnosis?: boolean | null;
  mapped_feature_count?: number;
  missing_feature_count?: number;
  defaulted_feature_count?: number;
  doctor_provided_feature_count?: number;
  source_ref_count?: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ModelInputSnapshotItem = ModelInputSnapshotSummaryItem & {
  preprocess_artifact_ref?: string | null;
  mapped_features?: Record<string, unknown> | null;
  missing_features?: unknown[];
  defaulted_features?: unknown[];
  doctor_provided_features?: unknown[];
  source_refs?: unknown[];
};

export type ModelInputSnapshotListResponse = {
  status?: string;
  route?: string;
  total: number;
  limit: number;
  offset: number;
  items: ModelInputSnapshotSummaryItem[];
};

export type ClinicalTableStrictValidationRequestV1 = {
  raw_columns: string[];
  rows: Array<Record<string, unknown>>;
  sample_row: Record<string, unknown>;
  source_type: 'csv_paste' | 'csv_upload_metadata' | 'manual_entry';
  not_for_diagnosis?: boolean;
  shadow_only?: boolean;
};

export type ClinicalTableStrictFeatureMappingItemV1 = {
  feature_order: number;
  model_feature_name: string;
  source_clinical_field: string;
  required: boolean;
  present: boolean;
  raw_column?: string | null;
  mapping_status: 'matched' | 'missing' | 'type_error';
  feature_type: string;
  unit?: string | null;
  coercion_status: 'ok' | 'missing' | 'type_error';
  sample_value?: unknown;
  coerced_value?: unknown;
  message?: string | null;
};

export type ClinicalTableStrictTypeCoercionItemV1 = {
  feature_order: number;
  model_feature_name: string;
  feature_type: string;
  row_count: number;
  coercion_status: 'ok' | 'missing' | 'type_error';
  sample_value?: unknown;
  coerced_value?: unknown;
  first_error_row_index?: number | null;
  message?: string | null;
};

export type ClinicalTableStrictValidationResponseV1 = {
  status?: string;
  route?: string;
  artifact_id: string;
  artifact_ref: string;
  artifact_feature_count: number;
  artifact_feature_order: string[];
  feature_mappings: ClinicalTableStrictFeatureMappingItemV1[];
  type_coercion_results: ClinicalTableStrictTypeCoercionItemV1[];
  missing_required_features: string[];
  extra_raw_columns: string[];
  validation_status: 'ready_for_inference' | 'schema_unverified' | 'insufficient_data_for_assessment';
  can_create_snapshot: boolean;
  order_matches_artifact: boolean;
  failure_reasons: string[];
  source_type: string;
  row_count: number;
  not_for_diagnosis: boolean;
  shadow_only: boolean;
  runtime_stub: boolean;
  limitations: string[];
};

export type ClinicalTableControlledSnapshotCreateRequestV1 = {
  raw_columns: string[];
  rows: Array<Record<string, unknown>>;
  sample_row: Record<string, unknown>;
  source_type: 'csv_paste' | 'csv_upload_metadata' | 'manual_entry';
  trace_id?: string | null;
  not_for_diagnosis?: boolean;
  shadow_only?: boolean;
};

export type ClinicalTableControlledSnapshotCreateResponseV1 = {
  status?: string;
  route?: string;
  artifact_id: string;
  artifact_ref: string;
  artifact_feature_count: number;
  artifact_feature_order: string[];
  validation_status: 'ready_for_inference' | 'schema_unverified' | 'insufficient_data_for_assessment';
  can_create_snapshot: boolean;
  order_matches_artifact: boolean;
  failure_reasons: string[];
  source_type: string;
  row_count: number;
  not_for_diagnosis: boolean;
  shadow_only: boolean;
  runtime_stub: boolean;
  snapshot_created: boolean;
  snapshot?: ModelInputSnapshotItem | null;
  mapped_features: Record<string, unknown>;
  source_refs: unknown[];
  doctor_provided_features: unknown[];
  limitations: string[];
};

export type ControlledShadowClinicalMlpFold5OneShotRequest = {
  input_snapshot_id: string;
  trace_id?: string | null;
  dry_run_label?: string | null;
};

export type ControlledShadowClinicalMlpFold5OneShotResponse = {
  status: string;
  route: string;
  execution_mode?: string;
  shadow_run_id: string;
  case_id: string;
  patient_id: string;
  trace_id: string;
  model_version_id: string;
  input_snapshot_id: string;
  not_for_diagnosis?: boolean;
  runtime_stub?: boolean;
  candidate_label?: string | null;
  prediction_probability_json?: Record<string, unknown>;
  confidence_json?: Record<string, unknown>;
  limitations_json?: Record<string, unknown>;
  error_code?: string | null;
};

function buildClinicalTableStrictValidationMock(caseId: string, payload: ClinicalTableStrictValidationRequestV1): ClinicalTableStrictValidationResponseV1 {
  const artifactOrder = payload.raw_columns.slice();
  const sampleRow = payload.sample_row || {};
  const row = payload.rows[0] || {};
  const featureMappings: ClinicalTableStrictFeatureMappingItemV1[] = artifactOrder.map((featureName, index) => {
    const rawValue = (row as Record<string, unknown>)[featureName];
    const present = rawValue !== undefined && rawValue !== null && rawValue !== '';
    return {
      feature_order: index + 1,
      model_feature_name: featureName,
      source_clinical_field: featureName,
      required: true,
      present,
      raw_column: featureName,
      mapping_status: present ? 'matched' : 'missing',
      feature_type: typeof rawValue === 'number' ? 'numeric' : typeof rawValue === 'boolean' ? 'boolean' : 'categorical',
      unit: null,
      coercion_status: present ? 'ok' : 'missing',
      sample_value: sampleRow[featureName] ?? null,
      coerced_value: present ? rawValue : null,
      message: present ? null : 'missing value',
    };
  });
  const missingRequiredFeatures = featureMappings.filter((item) => !item.present).map((item) => item.model_feature_name);
  const validationStatus = missingRequiredFeatures.length > 0 ? 'insufficient_data_for_assessment' : 'ready_for_inference';
  return {
    status: 'ok',
    route: '/api/v1/cases/' + caseId + '/model-input/clinical-table/validate',
    artifact_id: 'clinical_tabular_standardization_v1.json',
    artifact_ref: 'clinical_tabular_standardization_v1.json',
    artifact_feature_count: artifactOrder.length,
    artifact_feature_order: artifactOrder,
    feature_mappings: featureMappings,
    type_coercion_results: featureMappings.map((item) => ({
      feature_order: item.feature_order,
      model_feature_name: item.model_feature_name,
      feature_type: item.feature_type,
      row_count: payload.rows.length,
      coercion_status: item.coercion_status,
      sample_value: item.sample_value,
      coerced_value: item.coerced_value,
      first_error_row_index: item.present ? null : 0,
      message: item.message,
    })),
    missing_required_features: missingRequiredFeatures,
    extra_raw_columns: [],
    validation_status: validationStatus,
    can_create_snapshot: validationStatus === 'ready_for_inference',
    order_matches_artifact: true,
    failure_reasons: missingRequiredFeatures.length > 0 ? ['missing_required_features:' + missingRequiredFeatures.join(',')] : [],
    source_type: payload.source_type,
    row_count: payload.rows.length,
    not_for_diagnosis: true,
    shadow_only: true,
    runtime_stub: true,
    limitations: ['not_for_diagnosis', 'shadow_only', 'runtime_stub'],
  };
}

function buildClinicalTableSnapshotMock(caseId: string, payload: ClinicalTableControlledSnapshotCreateRequestV1): ClinicalTableControlledSnapshotCreateResponseV1 {
  const validation = buildClinicalTableStrictValidationMock(caseId, payload);
  const canCreate = validation.validation_status === 'ready_for_inference';
  const snapshot = canCreate ? ({
    id: 'snap_demo_' + caseId,
    input_snapshot_id: 'snap_demo_' + caseId,
    case_id: caseId,
    patient_id: 'patient-demo',
    trace_id: payload.trace_id || 'trace_demo',
    model_version_id: 'model-version-demo',
    model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
    disease_task_feature_set_id: 'cap_cop_clinical_feature_set_v1',
    validation_status: validation.validation_status,
    current_assessment_status: validation.validation_status,
    insufficient_data_for_assessment: false,
    runtime_stub: true,
    not_for_diagnosis: true,
    mapped_feature_count: payload.rows.length ? Object.keys(payload.rows[0] || {}).length : 0,
    missing_feature_count: validation.missing_required_features.length,
    defaulted_feature_count: 0,
    doctor_provided_feature_count: payload.rows.length ? Object.keys(payload.rows[0] || {}).length : 0,
    source_ref_count: payload.rows.length,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    preprocess_artifact_ref: 'clinical_tabular_standardization_v1.json',
    mapped_features: payload.rows[0] || {},
    missing_features: validation.missing_required_features,
    defaulted_features: [],
    doctor_provided_features: Object.keys(payload.rows[0] || {}),
    source_refs: payload.rows,
  } as ModelInputSnapshotItem) : null;
  return {
    status: 'ok',
    route: '/api/v1/cases/' + caseId + '/model-input/clinical-table/snapshots',
    artifact_id: validation.artifact_id,
    artifact_ref: validation.artifact_ref,
    artifact_feature_count: validation.artifact_feature_count,
    artifact_feature_order: validation.artifact_feature_order,
    validation_status: validation.validation_status,
    can_create_snapshot: canCreate,
    order_matches_artifact: validation.order_matches_artifact,
    failure_reasons: validation.failure_reasons,
    source_type: payload.source_type,
    row_count: payload.rows.length,
    not_for_diagnosis: true,
    shadow_only: true,
    runtime_stub: true,
    snapshot_created: canCreate,
    snapshot,
    mapped_features: payload.rows[0] || {},
    source_refs: payload.rows,
    doctor_provided_features: Object.keys(payload.rows[0] || {}),
    limitations: validation.limitations,
  };
}

export async function validateClinicalTableInput(caseId: string, payload: ClinicalTableStrictValidationRequestV1): Promise<ClinicalTableStrictValidationResponseV1> {
  if (API_MODE === 'mock') {
    return buildClinicalTableStrictValidationMock(caseId, payload);
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/model-input/clinical-table/validate', payload)).data;
  return data as ClinicalTableStrictValidationResponseV1;
}

export async function createClinicalTableSnapshotFromValidation(caseId: string, payload: ClinicalTableControlledSnapshotCreateRequestV1): Promise<ClinicalTableControlledSnapshotCreateResponseV1> {
  if (API_MODE === 'mock') {
    return buildClinicalTableSnapshotMock(caseId, payload);
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/model-input/clinical-table/snapshots', payload)).data;
  return unwrapItem<ClinicalTableControlledSnapshotCreateResponseV1>(data);
}

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

export async function createModelInputSnapshot(caseId: string, payload: ModelInputSnapshotCreatePayload): Promise<ModelInputSnapshotItem> {
  if (API_MODE === 'mock') {
    return {
      id: 'demo-snapshot-id',
      input_snapshot_id: 'snap_demo_' + caseId,
      case_id: caseId,
      patient_id: 'patient-demo',
      trace_id: payload.trace_id,
      model_version_id: payload.model_version_id,
      model_input_schema_id: payload.model_input_schema_id,
      disease_task_feature_set_id: payload.disease_task_feature_set_id,
      validation_status: payload.validation_status,
      current_assessment_status: payload.current_assessment_status,
      insufficient_data_for_assessment: payload.insufficient_data_for_assessment,
      runtime_stub: true,
      not_for_diagnosis: true,
      preprocess_artifact_ref: payload.preprocess_artifact_ref || null,
      mapped_features: payload.mapped_features,
      missing_features: payload.missing_features,
      defaulted_features: payload.defaulted_features,
      doctor_provided_features: payload.doctor_provided_features,
      source_refs: payload.source_refs,
      mapped_feature_count: Object.keys(payload.mapped_features || {}).length,
      missing_feature_count: payload.missing_features.length,
      defaulted_feature_count: payload.defaulted_features.length,
      doctor_provided_feature_count: payload.doctor_provided_features.length,
      source_ref_count: payload.source_refs.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/model-input-snapshots', payload)).data;
  return unwrapItem<ModelInputSnapshotItem>(data);
}

export async function listModelInputSnapshotsByCase(caseId: string, modelVersionId?: string, limit: number = 20, offset: number = 0): Promise<ModelInputSnapshotListResponse> {
  if (API_MODE === 'mock') {
    return {
      status: 'ok',
      route: '/api/v1/cases/' + caseId + '/model-input-snapshots',
      total: 1,
      limit,
      offset,
      items: [
        {
          id: 'demo-snapshot-id',
          input_snapshot_id: 'snap_demo_' + caseId,
          case_id: caseId,
          patient_id: 'patient-demo',
          trace_id: 'trace-demo',
          model_version_id: modelVersionId || 'capcop_stub_v1',
          model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
          disease_task_feature_set_id: 'cap_cop_clinical_feature_set_v1',
          validation_status: 'ready_for_inference',
          current_assessment_status: 'ready_for_inference',
          insufficient_data_for_assessment: false,
          runtime_stub: true,
          not_for_diagnosis: true,
          mapped_feature_count: 36,
          missing_feature_count: 0,
          defaulted_feature_count: 0,
          doctor_provided_feature_count: 36,
          source_ref_count: 1,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    };
  }
  const data = (await client.get('/api/v1/cases/' + caseId + '/model-input-snapshots', {
    params: {
      limit,
      offset,
      model_version_id: modelVersionId || undefined,
    },
  })).data;
  return data as ModelInputSnapshotListResponse;
}

export async function getModelInputSnapshot(inputSnapshotId: string): Promise<ModelInputSnapshotItem> {
  if (API_MODE === 'mock') {
    return {
      id: 'demo-snapshot-id',
      input_snapshot_id: inputSnapshotId,
      case_id: 'case-001',
      patient_id: 'patient-001',
      trace_id: 'trace-demo',
      model_version_id: 'capcop_stub_v1',
      model_input_schema_id: 'clinical_mlp_cap_cop_input_schema_v1',
      disease_task_feature_set_id: 'cap_cop_clinical_feature_set_v1',
      validation_status: 'ready_for_inference',
      current_assessment_status: 'ready_for_inference',
      insufficient_data_for_assessment: false,
      runtime_stub: true,
      not_for_diagnosis: true,
      preprocess_artifact_ref: 'clinical_tabular_standardization_v1.json',
      mapped_features: {},
      missing_features: [],
      defaulted_features: [],
      doctor_provided_features: [],
      source_refs: [],
      mapped_feature_count: 0,
      missing_feature_count: 0,
      defaulted_feature_count: 0,
      doctor_provided_feature_count: 0,
      source_ref_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  const data = (await client.get('/api/v1/model-input-snapshots/' + inputSnapshotId)).data;
  return unwrapItem<ModelInputSnapshotItem>(data);
}

export async function runClinicalMlpFold5OneShotShadow(caseId: string, payload: ControlledShadowClinicalMlpFold5OneShotRequest): Promise<ControlledShadowClinicalMlpFold5OneShotResponse> {
  if (API_MODE === 'mock') {
    return {
      status: 'completed',
      route: '/api/v1/cases/' + caseId + '/shadow-inference/clinical-mlp/fold5/one-shot',
      execution_mode: 'one_shot_fold5',
      shadow_run_id: 'shadow_mock_' + payload.input_snapshot_id.slice(-8),
      case_id: caseId,
      patient_id: 'patient-demo',
      trace_id: payload.trace_id || 'trace-demo',
      model_version_id: 'capcop_stub_v1',
      input_snapshot_id: payload.input_snapshot_id,
      not_for_diagnosis: true,
      runtime_stub: true,
      candidate_label: 'COP',
      prediction_probability_json: { CAP: 0, COP: 1 },
      confidence_json: { calibrated: false, value: 1 },
      limitations_json: {
        shadow_only: true,
        not_for_diagnosis: true,
        not_formal_recommendation: true,
        probability_uncalibrated: true,
        requires_doctor_review: true,
      },
      error_code: null,
    };
  }
  const data = (await client.post('/api/v1/cases/' + caseId + '/shadow-inference/clinical-mlp/fold5/one-shot', payload)).data;
  return data as ControlledShadowClinicalMlpFold5OneShotResponse;
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
  preprocessing_summary?: Record<string, unknown> | null;
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
  prototype_state?: string | null;
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
      prototype_state: 'prototype_not_executed',
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
      prototype_state: 'prototype_not_executed',
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
      prototype_state: 'prototype_not_executed',
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
          preprocessing_summary: { synthetic_only: true, runner_mode: 'metadata_only_stub' },
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



