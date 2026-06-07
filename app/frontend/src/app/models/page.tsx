'use client';

import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Form, Input, Select, Space, Table, Tag, Typography } from 'antd';
import {
  approveModelVersion,
  createModel,
  createModelVersion,
  getModel,
  getModelVersionEvaluations,
  listModels,
  promoteModelVersion,
  rollbackModelVersion,
  type ModelRegistryItem,
  type ModelVersionEvaluationsResponse,
  type ModelVersionItem,
} from '@/lib/api';

type ModelRow = ModelRegistryItem & { key: string };
type VersionRow = ModelVersionItem & { key: string };

type ModelFormValues = {
  model_name?: string;
  disease_agent?: string;
  task_type?: string;
  modality_scope?: string[];
  owner_team?: string;
  description?: string;
};

type VersionFormValues = {
  version_label?: string;
  artifact_ref?: string;
  notes?: string;
  metrics_json?: string;
  runtime_constraints_json?: string;
  input_schema_json?: string;
  output_schema_json?: string;
};

type RollbackFormValues = {
  version_id?: string;
  target_version_id?: string;
};

const T = (value: string) => value;

function parseJson<T>(raw?: string): T | undefined {
  if (!raw) return undefined;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return undefined;
  }
}

function normalizeError(error: unknown) {
  const response = (error as { response?: { status?: number; data?: { detail?: { code?: string } | string; code?: string } } })?.response;
  const code = response?.data?.detail && typeof response.data.detail === 'object' ? response.data.detail.code : response?.data?.code;
  if (code === 'model_not_found') return T('\u64cd\u4f5c\u5931\u8d25\uff1a\u6a21\u578b\u4e0d\u5b58\u5728');
  if (code === 'model_version_not_found') return T('\u64cd\u4f5c\u5931\u8d25\uff1a\u6a21\u578b\u7248\u672c\u4e0d\u5b58\u5728');
  if (code === 'invalid_lifecycle_state') return T('\u64cd\u4f5c\u5931\u8d25\uff1a\u751f\u547d\u5468\u671f\u72b6\u6001\u65e0\u6548');
  if (response?.status === 422) return T('\u64cd\u4f5c\u5931\u8d25\uff1a\u6a21\u578b\u5143\u6570\u636e\u6821\u9a8c\u672a\u901a\u8fc7');
  if (response?.status === 409) return T('\u64cd\u4f5c\u5931\u8d25\uff1a\u57fa\u7840\u8d44\u6599\u51b2\u7a81\u6216 default \u552f\u4e00\u6027\u88ab\u62d2\u7edd');
  if (response?.status === 404) return T('\u64cd\u4f5c\u5931\u8d25\uff1a\u540e\u7aef\u6a21\u578b\u7ba1\u7406\u63a5\u53e3\u4e0d\u53ef\u7528\uff08404\uff09');
  return T('\u64cd\u4f5c\u5931\u8d25\uff1a\u8bf7\u7a0d\u540e\u91cd\u8bd5');
}

function makeModelKey(item: ModelRegistryItem) {
  return item.model_id || item.model_name;
}

function makeVersionKey(item: ModelVersionItem) {
  return item.version_id || [item.model_id, item.version_label, item.created_at].filter(Boolean).join('|');
}

function versionStateColor(state?: string) {
  if (state === 'default') return 'green';
  if (state === 'canary') return 'blue';
  if (state === 'shadow') return 'gold';
  if (state === 'approved' || state === 'offline_evaluated') return 'cyan';
  if (state === 'deprecated' || state === 'archived') return 'default';
  return 'purple';
}

function renderCellText(value: unknown) {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  return JSON.stringify(value);
}

function renderJsonBlock(value: unknown) {
  return <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{JSON.stringify(value || {}, null, 2)}</pre>;
}

export default function Page() {
  const [modelForm] = Form.useForm<ModelFormValues>();
  const [versionForm] = Form.useForm<VersionFormValues>();
  const [rollbackForm] = Form.useForm<RollbackFormValues>();
  const [models, setModels] = useState<ModelRow[]>([]);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelRegistryItem | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState('');
  const [evaluations, setEvaluations] = useState<ModelVersionEvaluationsResponse['item'] | null>(null);
  const [loadingModels, setLoadingModels] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [busyAction, setBusyAction] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'info' | 'warning' | 'error'>('info');

  const versionRows = useMemo<VersionRow[]>(() => (selectedModel?.versions || []).map((item) => ({ ...item, key: makeVersionKey(item) })), [selectedModel]);

  async function loadModel(modelId: string, preferredVersionId?: string) {
    setLoadingDetail(true);
    try {
      const data = await getModel(modelId);
      setSelectedModel(data);
      setSelectedModelId(data.model_id);
      const nextVersionId = preferredVersionId || data.versions?.[0]?.version_id || '';
      setSelectedVersionId(nextVersionId);
      if (nextVersionId) {
        const evalData = await getModelVersionEvaluations(nextVersionId);
        setEvaluations(evalData.item);
      } else {
        setEvaluations(null);
      }
      rollbackForm.setFieldsValue({ version_id: nextVersionId || undefined, target_version_id: undefined });
    } catch (error) {
      setMessageType('error');
      setMessage(T('\u52a0\u8f7d\u6a21\u578b\u8be6\u60c5\u5931\u8d25\uff1a') + (error instanceof Error ? error.message : T('\u8bf7\u7a0d\u540e\u91cd\u8bd5')));
      setSelectedModel(null);
      setSelectedModelId('');
      setSelectedVersionId('');
      setEvaluations(null);
    } finally {
      setLoadingDetail(false);
    }
  }

  async function refreshModels(preferredModelId?: string) {
    setLoadingModels(true);
    try {
      const data = await listModels();
      const nextModels = (data.items || []).map((item) => ({ ...item, key: makeModelKey(item) }));
      setModels(nextModels);
      const nextSelectedId = preferredModelId || selectedModelId || nextModels[0]?.model_id || '';
      if (nextSelectedId) {
        const nextPreferredVersionId = nextSelectedId === selectedModelId ? selectedVersionId : '';
        await loadModel(nextSelectedId, nextPreferredVersionId);
      } else {
        setSelectedModel(null);
        setSelectedModelId('');
        setSelectedVersionId('');
        setEvaluations(null);
      }
    } catch (error) {
      setMessageType('error');
      setMessage(T('\u52a0\u8f7d\u6a21\u578b\u5217\u8868\u5931\u8d25\uff1a') + (error instanceof Error ? error.message : T('\u8bf7\u7a0d\u540e\u91cd\u8bd5')));
    } finally {
      setLoadingModels(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreateModel(values: ModelFormValues) {
    setBusyAction('create-model');
    setMessage('');
    try {
      const created = await createModel({
        model_name: values.model_name || '',
        disease_agent: values.disease_agent || '',
        task_type: values.task_type || '',
        modality_scope: values.modality_scope || [],
        owner_team: values.owner_team || '',
        description: values.description || '',
      });
      setMessageType('info');
      setMessage(T('\u6a21\u578b\u5143\u6570\u636e\u5df2\u521b\u5efa\uff0c\u672a\u52a0\u8f7d\u771f\u5b9e\u6a21\u578b\u3001\u672a\u89e6\u53d1\u8bad\u7ec3\u3001\u672a\u8bfb\u53d6 .pth\u3002'));
      modelForm.resetFields();
      await refreshModels(created.model_id);
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setBusyAction('');
    }
  }

  async function handleCreateVersion(values: VersionFormValues) {
    if (!selectedModelId) {
      setMessageType('warning');
      setMessage(T('\u8bf7\u5148\u9009\u62e9\u4e00\u4e2a\u6a21\u578b'));
      return;
    }
    setBusyAction('create-version');
    setMessage('');
    try {
      await createModelVersion(selectedModelId, {
        version_label: values.version_label || '',
        artifact_ref: values.artifact_ref || '',
        notes: values.notes || '',
        metrics: parseJson<Record<string, unknown>>(values.metrics_json),
        runtime_constraints: parseJson<Record<string, unknown>>(values.runtime_constraints_json),
        input_schema: parseJson<Record<string, unknown>>(values.input_schema_json),
        output_schema: parseJson<Record<string, unknown>>(values.output_schema_json),
      });
      setMessageType('info');
      setMessage(T('\u6a21\u578b\u7248\u672c\u5df2\u521b\u5efa\uff0cartifact_ref \u4ec5\u4f5c\u4e3a\u5143\u6570\u636e\u5b57\u7b26\u4e32\u4f7f\u7528\u3002'));
      versionForm.resetFields();
      await refreshModels(selectedModelId);
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setBusyAction('');
    }
  }

  async function handleApprove(versionId: string) {
    setBusyAction('approve-' + versionId);
    setMessage('');
    try {
      await approveModelVersion(versionId);
      setMessageType('info');
      setMessage(T('\u7248\u672c\u5df2\u6279\u51c6\u3002'));
      await refreshModels(selectedModelId);
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setBusyAction('');
    }
  }

  async function handlePromote(versionId: string, targetState: string) {
    setBusyAction('promote-' + versionId + '-' + targetState);
    setMessage('');
    try {
      await promoteModelVersion(versionId, targetState);
      setMessageType('info');
      setMessage(T('\u7248\u672c\u72b6\u6001\u5df2\u66f4\u65b0\u4e3a\uff1a') + targetState);
      await refreshModels(selectedModelId);
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setBusyAction('');
    }
  }

  async function handleRollback(values: RollbackFormValues) {
    if (!values.version_id || !values.target_version_id) {
      setMessageType('warning');
      setMessage(T('\u8bf7\u5148\u586b\u5199 version_id \u548c target_version_id'));
      return;
    }
    setBusyAction('rollback');
    setMessage('');
    try {
      await rollbackModelVersion(values.version_id, values.target_version_id);
      setMessageType('info');
      setMessage(T('\u7248\u672c\u56de\u6eda\u5df2\u63d0\u4ea4\u3002'));
      await refreshModels(selectedModelId);
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setBusyAction('');
    }
  }

  async function handleInspectVersion(versionId: string) {
    setSelectedVersionId(versionId);
    setBusyAction('inspect-' + versionId);
    setMessage('');
    try {
      const evalData = await getModelVersionEvaluations(versionId);
      setEvaluations(evalData.item);
      rollbackForm.setFieldsValue({ version_id: versionId });
      setMessageType('info');
      setMessage(T('\u5df2\u52a0\u8f7d\u7248\u672c\u8bc4\u4f30\u6458\u8981\u3002'));
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setBusyAction('');
    }
  }

  const modelDetailNotice = T('\u5f53\u524d\u53ea\u7ba1\u7406\u6a21\u578b\u5143\u6570\u636e\uff0c\u4e0d\u52a0\u8f7d\u771f\u5b9e\u6a21\u578b\uff0c\u4e0d\u89e6\u53d1\u8bad\u7ec3\uff0c\u4e0d\u8bfb\u53d6 .pth\uff1bshadow/canary/default \u53ea\u662f\u751f\u547d\u5468\u671f skeleton\uff0c\u4e0d\u662f\u771f\u5b9e\u6d41\u91cf\u8c03\u5ea6\u3002');

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>{T('\u6a21\u578b\u7ba1\u7406\u4e0e\u7248\u672c\u7ba1\u7406')}</Typography.Title>
      <Alert type='info' showIcon message={modelDetailNotice} />
      {message ? <Alert type={messageType} showIcon message={message} /> : null}

      <Card title={T('\u521b\u5efa\u6a21\u578b\u5143\u6570\u636e')}>
        <Form layout='vertical' form={modelForm} onFinish={handleCreateModel}>
          <Space size={16} wrap align='start' style={{ width: '100%' }}>
            <Form.Item label='model_name' name='model_name' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 model_name') }]} style={{ minWidth: 220 }}>
              <Input placeholder={T('\u4f8b\u5982\uff1ademo-capcop-model')} />
            </Form.Item>
            <Form.Item label='disease_agent' name='disease_agent' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 disease_agent') }]} style={{ minWidth: 220 }}>
              <Input placeholder={T('\u4f8b\u5982\uff1acapcop_agent')} />
            </Form.Item>
            <Form.Item label='task_type' name='task_type' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 task_type') }]} style={{ minWidth: 220 }}>
              <Input placeholder={T('\u4f8b\u5982\uff1arisk_assessment')} />
            </Form.Item>
            <Form.Item label='modality_scope' name='modality_scope' rules={[{ required: true, message: T('\u8bf7\u9009\u62e9 modality_scope') }]} style={{ minWidth: 240 }}>
              <Select
                mode='multiple'
                options={[
                  { label: 'ct', value: 'ct' },
                  { label: 'labs', value: 'labs' },
                  { label: 'clinical_table', value: 'clinical_table' },
                  { label: 'notes', value: 'notes' },
                  { label: 'ecg', value: 'ecg' },
                ]}
                placeholder={T('\u9009\u62e9\u9002\u7528\u6a21\u6001')}
              />
            </Form.Item>
            <Form.Item label='owner_team' name='owner_team' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 owner_team') }]} style={{ minWidth: 220 }}>
              <Input placeholder={T('\u4f8b\u5982\uff1adiagnostics')} />
            </Form.Item>
            <Form.Item label='description' name='description' style={{ minWidth: 360 }}>
              <Input.TextArea rows={3} placeholder={T('\u5143\u6570\u636e\u63cf\u8ff0\uff0c\u4ec5\u7528\u4e8e\u9875\u9762\u5c55\u793a')} />
            </Form.Item>
          </Space>
          <Button type='primary' htmlType='submit' loading={busyAction === 'create-model'}>{T('\u521b\u5efa demo model')}</Button>
        </Form>
      </Card>

      <Card title={T('\u6a21\u578b\u5217\u8868')}>
        <Table
          rowKey='model_id'
          loading={loadingModels}
          dataSource={models}
          pagination={false}
          scroll={{ x: 1400 }}
          onRow={(record) => ({ onClick: () => void loadModel(record.model_id) })}
          rowClassName={(record) => (record.model_id === selectedModelId ? 'ant-table-row-selected' : '')}
          columns={[
            { title: 'model_id', dataIndex: 'model_id', width: 220, render: (v: unknown) => renderCellText(v) },
            { title: 'model_name', dataIndex: 'model_name', width: 220, render: (v: unknown) => renderCellText(v) },
            { title: 'disease_agent', dataIndex: 'disease_agent', width: 180, render: (v: unknown) => renderCellText(v) },
            { title: 'task_type', dataIndex: 'task_type', width: 180, render: (v: unknown) => renderCellText(v) },
            { title: 'modality_scope', dataIndex: 'modality_scope', width: 220, render: (v: unknown) => Array.isArray(v) ? v.join(', ') : renderCellText(v) },
            { title: 'owner_team', dataIndex: 'owner_team', width: 180, render: (v: unknown) => renderCellText(v) },
            { title: 'is_active', dataIndex: 'is_active', width: 110, render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? T('\u662f') : T('\u5426')}</Tag> },
            { title: 'description', dataIndex: 'description', width: 320, render: (v: unknown) => renderCellText(v) },
          ]}
        />
      </Card>

      <Card title={T('\u5f53\u524d\u6a21\u578b\u8be6\u60c5')} loading={loadingDetail}>
        <Space direction='vertical' size={8} style={{ width: '100%' }}>
          <Typography.Text type='secondary'>{selectedModel ? T('\u5f53\u524d\u9009\u62e9\uff1a') + selectedModel.model_name : T('\u8bf7\u5148\u4ece\u4e0a\u65b9\u6a21\u578b\u5217\u8868\u9009\u62e9\u4e00\u4e2a\u6a21\u578b')}</Typography.Text>
          <Typography.Text type='secondary'>{modelDetailNotice}</Typography.Text>
        </Space>
      </Card>

      <Card title={T('\u521b\u5efa\u6a21\u578b\u7248\u672c')}>
        <Form layout='vertical' form={versionForm} onFinish={handleCreateVersion}>
          <Space size={16} wrap align='start' style={{ width: '100%' }}>
            <Form.Item label='version_label' name='version_label' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 version_label') }]} style={{ minWidth: 220 }}>
              <Input placeholder={T('\u4f8b\u5982\uff1av0.1.0')} />
            </Form.Item>
            <Form.Item label='artifact_ref' name='artifact_ref' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 artifact_ref') }]} style={{ minWidth: 360 }}>
              <Input placeholder={T('\u4f8b\u5982\uff1astub://artifacts/capcop/v0.1.0')} />
            </Form.Item>
            <Form.Item label='notes' name='notes' style={{ minWidth: 360 }}>
              <Input placeholder={T('\u7248\u672c\u8bf4\u660e\uff0c\u4ec5\u5143\u6570\u636e')} />
            </Form.Item>
            <Form.Item label='metrics_json' name='metrics_json' style={{ minWidth: 360 }}>
              <Input.TextArea rows={2} placeholder={T('\u4f8b\u5982\uff1a{"auc":0.82,"f1":0.71}')} />
            </Form.Item>
            <Form.Item label='runtime_constraints_json' name='runtime_constraints_json' style={{ minWidth: 360 }}>
              <Input.TextArea rows={2} placeholder={T('\u4f8b\u5982\uff1a{"cpu":"2","memory":"4Gi"}')} />
            </Form.Item>
            <Form.Item label='input_schema_json' name='input_schema_json' style={{ minWidth: 320 }}>
              <Input.TextArea rows={2} placeholder={T('\u8f93\u5165 schema JSON\uff0c\u53ef\u7559\u7a7a')} />
            </Form.Item>
            <Form.Item label='output_schema_json' name='output_schema_json' style={{ minWidth: 320 }}>
              <Input.TextArea rows={2} placeholder={T('\u8f93\u51fa schema JSON\uff0c\u53ef\u7559\u7a7a')} />
            </Form.Item>
          </Space>
          <Button type='primary' htmlType='submit' loading={busyAction === 'create-version'} disabled={!selectedModelId}>{T('\u521b\u5efa demo version')}</Button>
        </Form>
      </Card>

      <Card title={T('\u7248\u672c\u5217\u8868')}>
        <Table
          rowKey='version_id'
          loading={loadingDetail}
          dataSource={versionRows}
          pagination={false}
          scroll={{ x: 2200 }}
          columns={[
            { title: 'model_version_id', dataIndex: 'version_id', width: 220, render: (v: unknown) => renderCellText(v) },
            { title: 'version_label', dataIndex: 'version_label', width: 150, render: (v: unknown) => renderCellText(v) },
            { title: 'approval_state', dataIndex: 'approval_state', width: 150, render: (v: string) => <Tag color={versionStateColor(v)}>{renderCellText(v)}</Tag> },
            { title: 'artifact_ref', dataIndex: 'artifact_ref', width: 280, render: (v: unknown) => renderCellText(v) },
            { title: 'metrics', dataIndex: 'metrics', width: 240, render: (v: unknown) => renderJsonBlock(v) },
            { title: 'runtime_constraints', dataIndex: 'runtime_constraints', width: 280, render: (v: unknown) => renderJsonBlock(v) },
            { title: 'approved_by', dataIndex: 'approved_by', width: 180, render: (v: unknown) => renderCellText(v) },
            { title: 'approved_at', dataIndex: 'approved_at', width: 220, render: (v: unknown) => renderCellText(v) },
            { title: 'promoted_by', dataIndex: 'promoted_by', width: 180, render: (v: unknown) => renderCellText(v) },
            { title: 'promoted_at', dataIndex: 'promoted_at', width: 220, render: (v: unknown) => renderCellText(v) },
            {
              title: T('\u64cd\u4f5c'),
              dataIndex: 'version_id',
              width: 420,
              render: (_: string, row: VersionRow) => (
                <Space wrap>
                  <Button size='small' onClick={() => void handleInspectVersion(row.version_id)} loading={busyAction === 'inspect-' + row.version_id}>{T('\u67e5\u770b\u8bc4\u4f30')}</Button>
                  <Button size='small' onClick={() => void handleApprove(row.version_id)} loading={busyAction === 'approve-' + row.version_id}>{T('\u6279\u51c6')}</Button>
                  <Button size='small' onClick={() => void handlePromote(row.version_id, 'shadow')} loading={busyAction === 'promote-' + row.version_id + '-shadow'}>{T('\u8f6c shadow')}</Button>
                  <Button size='small' onClick={() => void handlePromote(row.version_id, 'canary')} loading={busyAction === 'promote-' + row.version_id + '-canary'}>{T('\u8f6c canary')}</Button>
                  <Button size='small' onClick={() => void handlePromote(row.version_id, 'default')} loading={busyAction === 'promote-' + row.version_id + '-default'}>{T('\u8f6c default')}</Button>
                </Space>
              )
            },
          ]}
        />
      </Card>

      <Card title={T('\u56de\u6eda\u4e0e\u8bc4\u4f30')}>
        <Form layout='vertical' form={rollbackForm} onFinish={handleRollback}>
          <Space size={16} wrap align='start' style={{ width: '100%' }}>
            <Form.Item label='version_id' name='version_id' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 version_id') }]} style={{ minWidth: 360 }}>
              <Input placeholder={T('\u8981\u56de\u6eda\u7684\u7248\u672c ID')} />
            </Form.Item>
            <Form.Item label='target_version_id' name='target_version_id' rules={[{ required: true, message: T('\u8bf7\u8f93\u5165 target_version_id') }]} style={{ minWidth: 360 }}>
              <Input placeholder={T('\u56de\u6eda\u76ee\u6807\u7248\u672c ID')} />
            </Form.Item>
          </Space>
          <Button htmlType='submit' loading={busyAction === 'rollback'}>{T('\u6267\u884c\u56de\u6eda')}</Button>
        </Form>
        <Space direction='vertical' size={8} style={{ width: '100%', marginTop: 16 }}>
          <Typography.Text strong>{T('\u8bc4\u4f30\u6458\u8981')}</Typography.Text>
          <Typography.Text type='secondary'>{selectedVersionId ? T('\u5f53\u524d\u67e5\u770b\u7248\u672c\uff1a') + selectedVersionId : T('\u8bf7\u70b9\u51fb\u201c\u67e5\u770b\u8bc4\u4f30\u201d\u52a0\u8f7d\u7248\u672c\u8bc4\u4f30\u6458\u8981')}</Typography.Text>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', background: '#fafafa', padding: 12, borderRadius: 6 }}>{JSON.stringify(evaluations || {}, null, 2)}</pre>
        </Space>
      </Card>
    </Space>
  );
}
