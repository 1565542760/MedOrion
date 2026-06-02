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

export const apiConfig = { mode: API_MODE, baseURL: API_BASE_URL };

const mock = {
  cases: [
    { case_id: 'case-001', patient_id: 'patient-001', disease_task: 'CAP', status: 'in_review', trace_id: 'trace-demo' },
    { case_id: 'case-002', patient_id: 'patient-002', disease_task: 'COP', status: 'awaiting_input', trace_id: 'trace-demo-2' }
  ],
  missingValues: [
    { field: 'procalcitonin', reason: 'lab_absent', suggested_options: ['???', '???????', '???????'] }
  ],
  recommendations: [
    { recommendation_id: 'rec-001', title: '???????????', risk_score: 0.78, trace_id: 'trace-demo' }
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
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  return [];
}

export async function getMissingValues(caseId: string, traceId?: string) {
  if (API_MODE === 'mock') return mock.missingValues;
  const url = '/api/v1/cases/' + caseId + '/missing-values';
  const data = (await client.get(url, withTraceId(traceId))).data;
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  return [];
}

export async function getRecommendations(caseId: string, traceId?: string) {
  if (API_MODE === 'mock') return mock.recommendations;
  const url = '/api/v1/cases/' + caseId + '/recommendations';
  const data = (await client.get(url, withTraceId(traceId))).data;
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  return [];
}

export async function getTrace(traceId: string) {
  if (API_MODE === 'mock') return { trace_id: traceId, status: 'completed' };
  const url = '/api/v1/traces/' + traceId;
  return (await client.get(url, withTraceId(traceId))).data;
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
