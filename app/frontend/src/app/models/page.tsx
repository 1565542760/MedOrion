'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Button, Card, Drawer, Form, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd';
import { WorkspaceTableShell } from '@/components/WorkspaceTableShell';
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

type ModelRow = ModelRegistryItem & {
  key: string;
  version_count: number;
  latest_version: string;
  latest_state: string;
  display_model_title: string;
  display_task_label: string;
  display_modality_label: string;
  is_seed_row?: boolean;
};

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

function parseJson<T>(raw?: string) {
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
  if (code === 'model_not_found') return '操作失败：模型不存在';
  if (code === 'model_version_not_found') return '操作失败：模型版本不存在';
  if (code === 'invalid_lifecycle_state') return '操作失败：生命周期状态无效';
  if (response?.status === 422) return '操作失败：模型元数据校验未通过';
  if (response?.status === 409) return '操作失败：基础资料冲突或 default 唯一性被拒绝';
  if (response?.status === 404) return '操作失败：后端模型管理接口不可用（404）';
  return '操作失败：请稍后重试';
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

const FORMAL_MODEL_ORDER = [
  'clinical_mlp_cap_cop_classifier',
  'imaging_resnet18_cap_cop_classifier',
  'multimodal_resnet18_cap_cop_classifier',
] as const;

const FORMAL_MODEL_INFO: Record<string, { title: string; hint: string }> = {
  clinical_mlp_cap_cop_classifier: { title: 'CAP/COP 临床模型', hint: '临床表格' },
  imaging_resnet18_cap_cop_classifier: { title: 'CAP/COP 影像模型', hint: '预处理 CT 影像' },
  multimodal_resnet18_cap_cop_classifier: { title: 'CAP/COP 多模态模型', hint: '临床表格 + 预处理 CT 影像' },
};

const TASK_LABELS: Record<string, string> = {
  risk_assessment: '风险评估',
};

const MODALITY_LABELS: Record<string, string> = {
  clinical_table: '临床表格',
  ct_nifti: '预处理 CT 影像',
  ct: '预处理 CT 影像',
};

function isFormalModel(model: ModelRegistryItem) {
  const key = model.model_name || '';
  return FORMAL_MODEL_ORDER.includes(key as (typeof FORMAL_MODEL_ORDER)[number]);
}

function formalModelInfo(model: ModelRegistryItem) {
  const key = model.model_name || '';
  return FORMAL_MODEL_INFO[key] || { title: 'CAP/COP 模型', hint: '正式模型' };
}

function taskLabel(taskType?: string | null) {
  if (!taskType) return '-';
  return TASK_LABELS[taskType] || '风险评估';
}

function modalityLabel(value?: string[] | string | null) {
  const items = Array.isArray(value) ? value : (value ? [value] : []);
  if (items.length === 0) return '-';
  return items.map((item) => MODALITY_LABELS[item] || item).join(' + ');
}

function versionStateLabel(state?: string) {
  switch ((state || '').toLowerCase()) {
    case 'default': return '默认版本';
    case 'canary': return '金丝雀版本';
    case 'shadow': return '影子版本';
    case 'approved': return '已批准';
    case 'offline_evaluated': return '离线评估通过';
    case 'deprecated': return '已弃用';
    case 'archived': return '已归档';
    case 'draft': return '草稿';
    default: return renderCellText(state);
  }
}

function sortVersions(versions?: ModelVersionItem[] | null) {
  return [...(versions || [])].sort((a, b) => new Date(b.published_at || b.created_at || 0).getTime() - new Date(a.published_at || a.created_at || 0).getTime());
}



function buildFormalModelSeedRows(): ModelRow[] {
  return FORMAL_MODEL_ORDER.map((model_name) => {
    const meta = FORMAL_MODEL_INFO[model_name];
    const modality_scope = model_name === 'clinical_mlp_cap_cop_classifier'
      ? ['clinical_table']
      : model_name === 'imaging_resnet18_cap_cop_classifier'
        ? ['ct_nifti']
        : ['clinical_table', 'ct_nifti'];
    return {
      model_id: model_name,
      model_name,
      disease_agent: 'capcop_agent',
      task_type: 'risk_assessment',
      modality_scope,
      owner_team: '-',
      description: '',
      is_active: true,
      created_at: '',
      updated_at: '',
      versions: [],
      key: model_name,
      version_count: 0,
      latest_version: '-',
      latest_state: '-',
      display_model_title: meta.title,
      display_task_label: taskLabel('risk_assessment'),
      display_modality_label: meta.hint,
      is_seed_row: true,
    } as ModelRow;
  });
}

export default function Page() {
  const [modelForm] = Form.useForm<ModelFormValues>();
  const [versionForm] = Form.useForm<VersionFormValues>();
  const [rollbackForm] = Form.useForm<RollbackFormValues>();

  const [models, setModels] = useState<ModelRow[]>(() => buildFormalModelSeedRows());
  const [selectedModelId, setSelectedModelId] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelRegistryItem | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState('');
  const [evaluations, setEvaluations] = useState<ModelVersionEvaluationsResponse['item'] | null>(null);

  const [loadingModels, setLoadingModels] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [busyAction, setBusyAction] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'info' | 'warning' | 'error'>('info');

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [createModelOpen, setCreateModelOpen] = useState(false);
  const [createVersionOpen, setCreateVersionOpen] = useState(false);
  const [rollbackOpen, setRollbackOpen] = useState(false);
  const initialLoadDoneRef = useRef(false);

  const versionRows = useMemo<VersionRow[]>(() => sortVersions(selectedModel?.versions).map((item) => ({ ...item, key: makeVersionKey(item) })), [selectedModel]);

  const loadModel = useCallback(async (modelId: string, openDrawer = false, preferredVersionId?: string) => {
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
      if (openDrawer) setDrawerOpen(true);
    } catch (error) {
      setMessageType('error');
      setMessage('加载模型详情失败：' + (error instanceof Error ? error.message : '请稍后重试'));
      setSelectedModel(null);
      setSelectedModelId('');
      setSelectedVersionId('');
      setEvaluations(null);
    } finally {
      setLoadingDetail(false);
    }
  }, [rollbackForm]);

  const refreshModels = useCallback(async (preferredModelId?: string) => {
    setLoadingModels(true);
    try {
      const data = await listModels();
      const nextModels = (data.items || [])
        .filter((item) => isFormalModel(item))
        .sort((a, b) => FORMAL_MODEL_ORDER.indexOf((a.model_name || '') as (typeof FORMAL_MODEL_ORDER)[number]) - FORMAL_MODEL_ORDER.indexOf((b.model_name || '') as (typeof FORMAL_MODEL_ORDER)[number]))
        .map((item) => {
          const versions = sortVersions(item.versions);
          const meta = formalModelInfo(item);
          return {
            ...item,
            versions,
            key: makeModelKey(item),
            version_count: versions.length,
            latest_version: versions[0]?.version_label || '-',
            latest_state: versions[0]?.approval_state || '-',
            display_model_title: meta.title,
            display_task_label: taskLabel(item.task_type),
            display_modality_label: modalityLabel(item.modality_scope),
            is_seed_row: false,
          };
        });
      setModels(nextModels);
      const nextSelectedId = preferredModelId || selectedModelId || nextModels[0]?.model_id || '';
      if (nextSelectedId) {
        const nextPreferredVersionId = nextSelectedId === selectedModelId ? selectedVersionId : '';
        await loadModel(nextSelectedId, false, nextPreferredVersionId);
      }
    } catch (error) {
      setMessageType('error');
      setMessage('加载模型列表失败：' + (error instanceof Error ? error.message : '请稍后重试'));
    } finally {
      setLoadingModels(false);
    }
  }, [loadModel, selectedModelId, selectedVersionId]);

  useEffect(() => {
    if (initialLoadDoneRef.current) return;
    initialLoadDoneRef.current = true;
    void refreshModels();
  }, [refreshModels]);

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
      setMessage('模型元数据已创建，未加载真实模型、未触发训练、未读取 .pth。');
      modelForm.resetFields();
      setCreateModelOpen(false);
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
      setMessage('请先选择一个模型');
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
      setMessage('模型版本已创建，artifact_ref 仅作元数据字符串使用。');
      versionForm.resetFields();
      setCreateVersionOpen(false);
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
      setMessage('版本已批准。');
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
      setMessage('版本状态已更新为：' + targetState);
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
      setMessage('请先填写 version_id 和 target_version_id');
      return;
    }
    setBusyAction('rollback');
    setMessage('');
    try {
      await rollbackModelVersion(values.version_id, values.target_version_id);
      setMessageType('info');
      setMessage('版本回滚已提交。');
      setRollbackOpen(false);
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
      setMessage('已加载版本评估摘要。');
    } catch (error) {
      setMessageType('error');
      setMessage(normalizeError(error));
    } finally {
      setBusyAction('');
    }
  }

  const notice = '当前页面仅展示 3 条正式 CAP/COP 模型。主表只看中文名称、任务和模态；英文 model_name、model_id、disease_agent 只在详情抽屉里显示。';

  return (
    <main style={{ padding: 24, width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <WorkspaceTableShell
        title='CAP/COP 模型管理'
        subtitle='主表只展示 3 条正式 CAP/COP 模型，任务和模态已中文化。英文标识留在详情抽屉。'
        actions={(
          <Space wrap>
            <Button onClick={() => { modelForm.resetFields(); setCreateModelOpen(true); }}>新建模型</Button>
            <Button onClick={() => { versionForm.resetFields(); setCreateVersionOpen(true); }} disabled={!selectedModelId}>新建版本</Button>
            <Button onClick={() => void refreshModels(selectedModelId)}>刷新</Button>
          </Space>
        )}
        minHeight={560}
      >
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Alert type='info' showIcon message={notice} />
          {message ? <Alert type={messageType} showIcon message={message} /> : null}
          <Table
            rowKey='model_id'
            loading={loadingModels}
            dataSource={models}
            pagination={false}
            size='small'
            sticky
            scroll={{ x: 1180, y: 'calc(100vh - 360px)' }}
            onRow={(record) => ({ onClick: record.is_seed_row ? undefined : () => void loadModel(record.model_id, true) })}
            rowClassName={(record) => (record.model_id === selectedModelId ? 'ant-table-row-selected' : '')}
            columns={[
              { title: '正式模型', dataIndex: 'display_model_title', width: 220, render: (_value: unknown, row: ModelRow) => (<Space direction='vertical' size={0}><Typography.Text strong>{row.display_model_title}</Typography.Text><Typography.Text type='secondary' style={{ fontSize: 12 }}>{row.display_task_label}</Typography.Text></Space>) },
              { title: '病种任务', dataIndex: 'display_task_label', width: 150, render: (value: unknown) => renderCellText(value) },
              { title: '模态范围', dataIndex: 'display_modality_label', width: 220, render: (value: unknown) => renderCellText(value) },
              { title: '版本数', dataIndex: 'version_count', width: 90 },
              { title: '状态', dataIndex: 'is_active', width: 120, render: (value: boolean) => <Tag color={value ? 'green' : 'default'}>{value ? '启用' : '停用'}</Tag> },
              { title: '最近版本', dataIndex: 'latest_version', width: 150, render: (value: unknown) => renderCellText(value) },
              { title: '最近状态', dataIndex: 'latest_state', width: 130, render: (value: string) => <Tag color={versionStateColor(value)}>{versionStateLabel(value)}</Tag> },
              {
                title: '操作',
                width: 120,
                render: (_: unknown, row: ModelRow) => (
                  <Button size='small' onClick={(event) => { event.stopPropagation(); void loadModel(row.model_id, true); }}>查看</Button>
                ),
              },
            ]}
          />
        </Space>
      </WorkspaceTableShell>

      <Drawer
        title={selectedModel ? '模型详情：' + formalModelInfo(selectedModel).title : '模型详情'}
        width={960}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        {selectedModel ? (
          <Space direction='vertical' size={16} style={{ width: '100%' }}>
            <Alert type='info' showIcon message={notice} />
            <Alert type='info' showIcon message='英文 model_name、model_id、disease_agent 仅在技术信息区展示。' />
            <Space wrap>
              <Tag color='blue'>正式名称：{formalModelInfo(selectedModel).title}</Tag>
              <Tag color='green'>模态：{modalityLabel(selectedModel.modality_scope as string[] | string | null)}</Tag>
              <Tag color='cyan'>负责人：{renderCellText(selectedModel.owner_team)}</Tag>
              <Tag color={selectedModel.is_active ? 'green' : 'default'}>{selectedModel.is_active ? '启用中' : '已停用'}</Tag>
            </Space>
            <Typography.Text type='secondary'>{renderCellText(selectedModel.description)}</Typography.Text>

            <Card size='small' title='技术信息' style={{ width: '100%' }}>
              <Space direction='vertical' size={4}>
                <Typography.Text>英文 model_name：{renderCellText(selectedModel.model_name)}</Typography.Text>
                <Typography.Text>模型 ID：{renderCellText(selectedModel.model_id)}</Typography.Text>
                <Typography.Text>疾病代理：{renderCellText(selectedModel.disease_agent)}</Typography.Text>
                <Typography.Text>任务类型：{renderCellText(selectedModel.task_type)}</Typography.Text>
                <Typography.Text>模态原始值：{renderCellText(selectedModel.modality_scope)}</Typography.Text>
              </Space>
            </Card>

            <Space wrap>
              <Button onClick={() => { versionForm.resetFields(); setCreateVersionOpen(true); }} disabled={!selectedModelId}>新建版本</Button>
              <Button onClick={() => { rollbackForm.resetFields(); setRollbackOpen(true); }} disabled={!selectedVersionId}>回滚</Button>
            </Space>

            <Table
              rowKey='version_id'
              loading={loadingDetail}
              dataSource={versionRows}
              pagination={false}
              size='small'
              sticky
              scroll={{ x: 1180, y: 280 }}
              columns={[
                { title: '版本', dataIndex: 'version_label', width: 150, render: (value: unknown, row: VersionRow) => (<Space direction='vertical' size={0}><Typography.Text strong>{renderCellText(value)}</Typography.Text><Typography.Text type='secondary' style={{ fontSize: 12 }}>{row.version_id}</Typography.Text></Space>) },
                { title: '状态', dataIndex: 'approval_state', width: 130, render: (value: string) => <Tag color={versionStateColor(value)}>{versionStateLabel(value)}</Tag> },
                { title: '工件引用', dataIndex: 'artifact_ref', width: 280, render: (value: unknown) => renderCellText(value) },
                { title: '发布时间', dataIndex: 'published_at', width: 180, render: (value: unknown) => renderCellText(value) },
                {
                  title: '操作',
                  width: 360,
                  render: (_: unknown, row: VersionRow) => (
                    <Space wrap>
                      <Button size='small' onClick={() => void handleInspectVersion(row.version_id)} loading={busyAction === 'inspect-' + row.version_id}>查看评估</Button>
                      <Button size='small' onClick={() => void handleApprove(row.version_id)} loading={busyAction === 'approve-' + row.version_id}>批准</Button>
                      <Button size='small' onClick={() => void handlePromote(row.version_id, 'shadow')} loading={busyAction === 'promote-' + row.version_id + '-shadow'}>转 shadow</Button>
                      <Button size='small' onClick={() => void handlePromote(row.version_id, 'default')} loading={busyAction === 'promote-' + row.version_id + '-default'}>转 default</Button>
                    </Space>
                  ),
                },
              ]}
            />

            <Typography.Title level={5} style={{ margin: 0 }}>版本评估摘要</Typography.Title>
            <Typography.Text type='secondary'>当前版本：{selectedVersionId || '-'}</Typography.Text>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', background: '#fafafa', padding: 12, borderRadius: 8 }}>{JSON.stringify(evaluations || {}, null, 2)}</pre>
          </Space>
        ) : (
          <Typography.Text>请先从主表选择一个模型。</Typography.Text>
        )}
      </Drawer>

      <Modal title='新建模型' open={createModelOpen} onCancel={() => setCreateModelOpen(false)} onOk={() => void modelForm.submit()} confirmLoading={busyAction === 'create-model'} okText='创建'>
        <Form layout='vertical' form={modelForm} onFinish={handleCreateModel}>
          <Form.Item label='model_name' name='model_name' rules={[{ required: true, message: '请输入 model_name' }]}><Input placeholder='例如：demo-capcop-model' /></Form.Item>
          <Form.Item label='disease_agent' name='disease_agent' rules={[{ required: true, message: '请输入 disease_agent' }]}><Input placeholder='例如：capcop_agent' /></Form.Item>
          <Form.Item label='task_type' name='task_type' rules={[{ required: true, message: '请输入 task_type' }]}><Input placeholder='例如：risk_assessment' /></Form.Item>
          <Form.Item label='modality_scope' name='modality_scope' rules={[{ required: true, message: '请选择 modality_scope' }]}>
            <Select mode='multiple' options={[{ label: 'ct', value: 'ct' }, { label: 'labs', value: 'labs' }, { label: 'clinical_table', value: 'clinical_table' }, { label: 'notes', value: 'notes' }, { label: 'ecg', value: 'ecg' }]} placeholder='选择适用模态' />
          </Form.Item>
          <Form.Item label='owner_team' name='owner_team' rules={[{ required: true, message: '请输入 owner_team' }]}><Input placeholder='例如：diagnostics' /></Form.Item>
          <Form.Item label='description' name='description'><Input.TextArea rows={3} placeholder='仅用于页面展示的元数据说明' /></Form.Item>
        </Form>
      </Modal>

      <Modal title='新建版本' open={createVersionOpen} onCancel={() => setCreateVersionOpen(false)} onOk={() => void versionForm.submit()} confirmLoading={busyAction === 'create-version'} okText='创建'>
        <Form layout='vertical' form={versionForm} onFinish={handleCreateVersion}>
          <Form.Item label='version_label' name='version_label' rules={[{ required: true, message: '请输入 version_label' }]}><Input placeholder='例如：v0.1.0' /></Form.Item>
          <Form.Item label='artifact_ref' name='artifact_ref' rules={[{ required: true, message: '请输入 artifact_ref' }]}><Input placeholder='例如：stub://artifacts/capcop/v0.1.0' /></Form.Item>
          <Form.Item label='notes' name='notes'><Input placeholder='版本说明，仅元数据' /></Form.Item>
          <Form.Item label='metrics_json' name='metrics_json'><Input.TextArea rows={2} placeholder='例如：{"auc":0.82,"f1":0.71}' /></Form.Item>
          <Form.Item label='runtime_constraints_json' name='runtime_constraints_json'><Input.TextArea rows={2} placeholder='例如：{"cpu":"2","memory":"4Gi"}' /></Form.Item>
          <Form.Item label='input_schema_json' name='input_schema_json'><Input.TextArea rows={2} placeholder='输入 schema JSON，可留空' /></Form.Item>
          <Form.Item label='output_schema_json' name='output_schema_json'><Input.TextArea rows={2} placeholder='输出 schema JSON，可留空' /></Form.Item>
        </Form>
      </Modal>

      <Modal title='版本回滚' open={rollbackOpen} onCancel={() => setRollbackOpen(false)} onOk={() => void rollbackForm.submit()} confirmLoading={busyAction === 'rollback'} okText='执行回滚'>
        <Form layout='vertical' form={rollbackForm} onFinish={handleRollback}>
          <Form.Item label='version_id' name='version_id' rules={[{ required: true, message: '请输入 version_id' }]}><Input placeholder='要回滚的版本 ID' /></Form.Item>
          <Form.Item label='target_version_id' name='target_version_id' rules={[{ required: true, message: '请输入 target_version_id' }]}><Input placeholder='回滚目标版本 ID' /></Form.Item>
        </Form>
      </Modal>
    </main>
  );
}
