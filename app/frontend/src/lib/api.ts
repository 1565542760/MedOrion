import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

type ApiMode = 'mock' | 'backend';

const API_MODE = (process.env.NEXT_PUBLIC_API_MODE || 'backend') as ApiMode;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

const client = axios.create({ baseURL: API_BASE_URL, timeout: 10000 });

client.interceptors.request.use((config) => {
  config.headers.set('x-request-id', uuidv4());
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
    { field: 'procalcitonin', reason: 'lab_absent', suggested_options: ['补采血', '医生确认无该项', '以临床判断替代'] }
  ],
  recommendations: [
    { recommendation_id: 'rec-001', title: '建议完善感染指标后复评', risk_score: 0.78, trace_id: 'trace-demo' }
  ]
};

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
