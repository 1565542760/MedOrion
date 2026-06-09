'use client';

import Link from 'next/link';
import { use, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Checkbox, Col, Descriptions, Form, Input, Row, Select, Space, Table, Tag, Typography } from 'antd';
import {
  createCaseImagingInput,
  getCaseImagingInput,
  listCaseImagingInputs,
  listCases,
  listModelInputSnapshotsByCase,
  listShadowRunsByCase,
  type CaseImagingInputItem,
  type CaseItem,
  type ModelInputSnapshotSummaryItem,
  type ShadowInferenceRunItem,
} from '@/lib/api';

type ImagingFormValues = {
  trace_id?: string;
  modality?: string;
  source_type?: string;
  storage_uri?: string;
  provenance_json?: string;
  quality_flags_json?: string;
};

function safeParseJson(text?: string) {
  const trimmed = (text || '').trim();
  if (!trimmed) return {};
  try {
    return JSON.parse(trimmed) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function prettyJson(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

function getModalityLabel(value?: string | null) {
  switch (value || '') {
    case 'CT':
      return 'CT';
    case 'NIfTI':
      return 'NIfTI';
    case 'demo_image':
      return '演示影像';
    case 'synthetic_visual_sample':
      return '合成影像样本';
    default:
      return value || '-';
  }
}

function getSourceTypeLabel(value?: string | null) {
  switch (value || '') {
    case 'real_deidentified':
      return '脱敏真实影像';
    case 'synthetic':
      return '合成样本';
    case 'demo':
      return '课程演示';
    default:
      return value || '-';
  }
}

function getTwinLabel(count: number, shadowCount: number) {
  if (count > 0 && shadowCount > 0) return '课程演示 twin 可查看';
  if (count > 0) return '影像输入已登记';
  return '待建立';
}

function getBaselineLabel(count: number) {
  if (count > 0) return '表格 baseline 已建立';
  return '表格 baseline 待建立';
}

function getShadowLabel(count: number) {
  if (count > 0) return 'Shadow 已就绪';
  return 'Shadow 待建立';
}

function getImagingStateLabel(count: number) {
  if (count > 0) return '已登记';
  return '待登记';
}

function renderJsonBlock(value: unknown) {
  return (
    <pre
      style={{
        margin: 0,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        background: '#fafafa',
        border: '1px solid #f0f0f0',
        borderRadius: 6,
        padding: 12,
        maxWidth: '100%',
      }}
    >
      {prettyJson(value)}
    </pre>
  );
}

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [form] = Form.useForm<ImagingFormValues>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'info' | 'warning' | 'error'>('info');
  const [caseRecord, setCaseRecord] = useState<CaseItem | null>(null);
  const [items, setItems] = useState<CaseImagingInputItem[]>([]);
  const [details, setDetails] = useState<Record<string, CaseImagingInputItem>>({});
  const [snapshots, setSnapshots] = useState<ModelInputSnapshotSummaryItem[]>([]);
  const [shadowRuns, setShadowRuns] = useState<ShadowInferenceRunItem[]>([]);

  const demoValues = useMemo(() => ({
    trace_id: caseRecord?.trace_id || 'trace-demo',
    modality: 'CT',
    source_type: 'demo',
    storage_uri: 'managed://coursework-demo/' + caseId + '/ct-series-01',
    provenance_json: JSON.stringify({
      origin: 'coursework-demo',
      capture_mode: 'manual-registration',
      source_case_link: caseId,
    }, null, 2),
    quality_flags_json: JSON.stringify({
      artifact_free: true,
      slice_count_ok: true,
      orientation_ok: true,
    }, null, 2),
  }), [caseId, caseRecord?.trace_id]);

  async function loadPageState() {
    setLoading(true);
    try {
      const [casesResult, imagingResult, snapshotResult, shadowResult] = await Promise.allSettled([
        listCases(),
        listCaseImagingInputs(caseId),
        listModelInputSnapshotsByCase(caseId),
        listShadowRunsByCase(caseId),
      ]);

      const caseItem = casesResult.status === 'fulfilled'
        ? (casesResult.value || []).find((item) => item.case_id === caseId) || null
        : null;
      const imagingItems = imagingResult.status === 'fulfilled' ? imagingResult.value.items || [] : [];
      const snapshotItems = snapshotResult.status === 'fulfilled' ? snapshotResult.value.items || [] : [];
      const shadowItems = shadowResult.status === 'fulfilled' ? shadowResult.value.items || [] : [];

      setCaseRecord(caseItem);
      setItems(imagingItems);
      setSnapshots(snapshotItems);
      setShadowRuns(shadowItems);

      if (imagingItems.length > 0) {
        setDetails((current) => ({ ...current, ...Object.fromEntries(imagingItems.map((item) => [item.input_asset_id, item])) }));
      }
    } catch {
      setMessageType('error');
      setMessage('影像输入页面加载失败，请确认后端服务和登录状态。');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [casesResult, imagingResult, snapshotResult, shadowResult] = await Promise.allSettled([
          listCases(),
          listCaseImagingInputs(caseId),
          listModelInputSnapshotsByCase(caseId),
          listShadowRunsByCase(caseId),
        ]);

        if (!active) return;

        const caseItem = casesResult.status === 'fulfilled'
          ? (casesResult.value || []).find((item) => item.case_id === caseId) || null
          : null;
        const imagingItems = imagingResult.status === 'fulfilled' ? imagingResult.value.items || [] : [];
        const snapshotItems = snapshotResult.status === 'fulfilled' ? snapshotResult.value.items || [] : [];
        const shadowItems = shadowResult.status === 'fulfilled' ? shadowResult.value.items || [] : [];

        setCaseRecord(caseItem);
        setItems(imagingItems);
        setSnapshots(snapshotItems);
        setShadowRuns(shadowItems);

        if (imagingItems.length > 0) {
          setDetails((current) => ({ ...current, ...Object.fromEntries(imagingItems.map((item) => [item.input_asset_id, item])) }));
        }
      } catch {
        if (!active) return;
        setMessageType('error');
        setMessage('影像输入页面加载失败，请确认后端服务和登录状态。');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [caseId]);

  async function handleSubmit(values: ImagingFormValues) {
    setSaving(true);
    setMessage('');

    const provenanceJson = safeParseJson(values.provenance_json);
    if (provenanceJson === null) {
      setMessageType('error');
      setMessage('provenance_json 不是合法 JSON，请先修正后再保存。');
      setSaving(false);
      return;
    }

    const qualityFlagsJson = safeParseJson(values.quality_flags_json);
    if (qualityFlagsJson === null) {
      setMessageType('error');
      setMessage('quality_flags_json 不是合法 JSON，请先修正后再保存。');
      setSaving(false);
      return;
    }

    try {
      const item = await createCaseImagingInput(caseId, {
        patient_id: caseRecord?.patient_id || undefined,
        trace_id: values.trace_id || caseRecord?.trace_id || null,
        modality: values.modality || 'CT',
        source_type: values.source_type || 'demo',
        storage_uri: values.storage_uri || '',
        deidentified: true,
        not_for_diagnosis: true,
        provenance_json: provenanceJson,
        quality_flags_json: qualityFlagsJson,
      });
      setDetails((current) => ({ ...current, [item.input_asset_id]: item }));
      setMessageType('success');
      setMessage('影像输入元数据已登记：' + item.input_asset_id);
      form.resetFields();
      await loadPageState();
    } catch (error) {
      setMessageType('error');
      setMessage('影像输入登记失败：' + (error instanceof Error ? error.message : '请稍后重试'));
    } finally {
      setSaving(false);
    }
  }

  async function handleDemoFill() {
    form.setFieldsValue(demoValues);
    setMessageType('info');
    setMessage('已填入课程演示样例，仅用于元数据登记，不代表真实临床影像。');
  }

  async function handleExpand(expanded: boolean, record: CaseImagingInputItem) {
    if (!expanded || details[record.input_asset_id]) return;
    try {
      const detail = await getCaseImagingInput(record.input_asset_id);
      setDetails((current) => ({ ...current, [record.input_asset_id]: detail }));
    } catch {
      setDetails((current) => ({ ...current, [record.input_asset_id]: record }));
    }
  }

  const digitalTwinSummary = getTwinLabel(items.length, shadowRuns.length);

  return (
    <Space direction='vertical' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }} size={16}>
      <Space direction='vertical' size={2}>
        <Typography.Title level={4} style={{ margin: 0 }}>影像输入 / 数字孪生</Typography.Title>
        <Typography.Text type='secondary'>病例：{caseId}</Typography.Text>
      </Space>

      <Alert
        type='info'
        showIcon
        message='这里只登记影像 metadata / reference，不上传真实文件'
        description='deidentified 和 not_for_diagnosis 固定为 true。页面仅用于课程演示、shadow 旁路和数字孪生入口，不构成临床诊断，也不触发模型运行。'
      />

      {message ? (
        <Alert
          type={messageType}
          showIcon
          message={message}
        />
      ) : null}

      <Card
        size='small'
        title='病例上下文'
        extra={<Space wrap size={8}><Link href='/cases'>返回病例列表</Link><Link href={'/cases/' + caseId + '/model-input'}>CAP/COP 特征与输入快照</Link><Link href={'/cases/' + caseId + '/shadow-audit'}>Shadow 审计</Link></Space>}
        style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}
      >
        <Descriptions bordered size='small' column={2}>
          <Descriptions.Item label='病例 ID'>{caseRecord?.case_id || caseId}</Descriptions.Item>
          <Descriptions.Item label='病例编号'>{caseRecord?.case_no || '-'}</Descriptions.Item>
          <Descriptions.Item label='患者 ID'>{caseRecord?.patient_id || '-'}</Descriptions.Item>
          <Descriptions.Item label='Trace / 溯源'>{caseRecord?.trace_id || '-'}</Descriptions.Item>
          <Descriptions.Item label='病种任务'>{caseRecord?.disease_task || '-'}</Descriptions.Item>
          <Descriptions.Item label='当前状态'>{caseRecord?.status || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        size='small'
        title='登记影像元数据'
        style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}
        extra={<Button onClick={handleDemoFill}>填充课程演示样例</Button>}
      >
        <Form form={form} layout='vertical' onFinish={handleSubmit} initialValues={demoValues}>
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label='Trace / 溯源 ID' name='trace_id' rules={[{ required: true, message: '请输入 trace_id' }]}>
                <Input placeholder='例如：trace-demo' />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label='模态' name='modality' rules={[{ required: true, message: '请选择模态' }]}>
                <Select
                  options={[
                    { label: 'CT', value: 'CT' },
                    { label: 'NIfTI', value: 'NIfTI' },
                    { label: '演示影像', value: 'demo_image' },
                    { label: '合成影像样本', value: 'synthetic_visual_sample' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label='来源类型' name='source_type' rules={[{ required: true, message: '请选择来源类型' }]}>
                <Select
                  options={[
                    { label: '脱敏真实影像', value: 'real_deidentified' },
                    { label: '合成样本', value: 'synthetic' },
                    { label: '课程演示', value: 'demo' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label='存储 URI / 参考位置' name='storage_uri' rules={[{ required: true, message: '请输入 storage_uri' }]}>
            <Input placeholder='例如：managed://coursework-demo/case-001/ct-series-01' />
          </Form.Item>

          <Space wrap size={16} style={{ marginBottom: 16 }}>
            <Checkbox checked disabled>deidentified = true</Checkbox>
            <Checkbox checked disabled>not_for_diagnosis = true</Checkbox>
          </Space>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label='provenance_json'
                name='provenance_json'
                extra='仅填写来源与处理说明，不写真实影像文件路径。'
              >
                <Input.TextArea rows={8} spellCheck={false} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                label='quality_flags_json'
                name='quality_flags_json'
                extra='用于记录课程演示质量标记，不影响诊断。'
              >
                <Input.TextArea rows={8} spellCheck={false} />
              </Form.Item>
            </Col>
          </Row>

          <Space wrap size={8}>
            <Button type='primary' htmlType='submit' loading={saving}>登记影像输入元数据</Button>
            <Typography.Text type='secondary'>保存后不会自动诊断，也不会生成 shadow recommendation。</Typography.Text>
          </Space>
        </Form>
      </Card>

      <Card
        size='small'
        title='影像输入列表'
        style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}
      >
        <Space direction='vertical' size={8} style={{ width: '100%' }}>
          <Typography.Text type='secondary'>
            当前仅展示 metadata / reference summary。点击行左侧展开可看 provenance 和 quality flags。
          </Typography.Text>
          <div style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
            <Table
              rowKey='input_asset_id'
              loading={loading}
              dataSource={items}
              pagination={false}
              scroll={{ x: 1380 }}
              expandable={{
                expandedRowRender: (record) => {
                  const detail = details[record.input_asset_id] || record;
                  return (
                    <div style={{ margin: 0, width: '100%', maxWidth: '100%', overflowX: 'hidden', padding: 12, border: '1px solid #f0f0f0', borderRadius: 8, background: '#fafafa' }}>
                      <Row gutter={16}>
                        <Col xs={24} md={12}>
                          <Typography.Title level={5} style={{ marginTop: 0 }}>provenance_json</Typography.Title>
                          {renderJsonBlock(detail.provenance_json)}
                        </Col>
                        <Col xs={24} md={12}>
                          <Typography.Title level={5} style={{ marginTop: 0 }}>quality_flags_json</Typography.Title>
                          {renderJsonBlock(detail.quality_flags_json)}
                        </Col>
                      </Row>
                    </div>
                  );
                },
                onExpand: handleExpand,
              }}
              locale={{
                emptyText: (
                  <Space direction='vertical' size={4}>
                    <Typography.Text>暂无影像输入记录</Typography.Text>
                    <Typography.Text type='secondary'>可以先填充课程演示样例，再登记一条 metadata/reference。</Typography.Text>
                  </Space>
                ),
              }}
              columns={[
                { title: '输入资产 ID', dataIndex: 'input_asset_id', width: 220, render: (value: string) => value || '-' },
                { title: '模态', dataIndex: 'modality', width: 120, render: (value: string) => <Tag>{getModalityLabel(value)}</Tag> },
                { title: '来源类型', dataIndex: 'source_type', width: 150, render: (value: string) => <Tag>{getSourceTypeLabel(value)}</Tag> },
                { title: '存储 URI', dataIndex: 'storage_uri', width: 280, render: (value: string) => <Typography.Text>{value || '-'}</Typography.Text> },
                { title: '脱敏', dataIndex: 'deidentified', width: 90, render: (value: boolean) => <Tag color={value ? 'green' : 'red'}>{value ? 'true' : 'false'}</Tag> },
                { title: '非诊断', dataIndex: 'not_for_diagnosis', width: 90, render: (value: boolean) => <Tag color={value ? 'green' : 'red'}>{value ? 'true' : 'false'}</Tag> },
                { title: 'Trace / 溯源', dataIndex: 'trace_id', width: 220, render: (value: string) => value || '-' },
                { title: '创建时间', dataIndex: 'created_at', width: 180, render: (value: string) => value || '-' },
              ]}
            />
          </div>
        </Space>
      </Card>

      <Card
        size='small'
        title='病例级数字孪生骨架'
        style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}
      >
        <Alert
          type='warning'
          showIcon
          message='课程演示 / shadow / 非诊断 / 非正式推荐'
          description='这里仅展示病例级肺部状态 twin 的入口骨架，不上传真实影像，不触发模型，不写 recommendation，也不写 trace/evidence。'
        />
        <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
          <Col xs={24} md={6}>
            <div style={{ height: '100%', border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
              <Space direction='vertical' size={4}>
                <Typography.Text type='secondary'>影像输入状态</Typography.Text>
                <Tag color={items.length > 0 ? 'green' : 'default'}>{getImagingStateLabel(items.length)}</Tag>
                <Typography.Text>{items.length > 0 ? '仅登记 metadata / reference。' : '尚未登记影像输入元数据。'}</Typography.Text>
              </Space>
            </div>
          </Col>
          <Col xs={24} md={6}>
            <div style={{ height: '100%', border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
              <Space direction='vertical' size={4}>
                <Typography.Text type='secondary'>表格 baseline 状态</Typography.Text>
                <Tag color={snapshots.length > 0 ? 'green' : 'default'}>{getBaselineLabel(snapshots.length)}</Tag>
                <Typography.Text>{snapshots.length > 0 ? '表格 baseline 已有输入快照，可继续做课程联调。' : '请先补齐表格 baseline 输入快照。'}</Typography.Text>
              </Space>
            </div>
          </Col>
          <Col xs={24} md={6}>
            <div style={{ height: '100%', border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
              <Space direction='vertical' size={4}>
                <Typography.Text type='secondary'>Shadow 状态</Typography.Text>
                <Tag color={shadowRuns.length > 0 ? 'green' : 'default'}>{getShadowLabel(shadowRuns.length)}</Tag>
                <Typography.Text>{shadowRuns.length > 0 ? '已有旁路审计记录，可在 Shadow 页面查看。' : '该页面不触发运行，只展示入口骨架。'}</Typography.Text>
              </Space>
            </div>
          </Col>
          <Col xs={24} md={6}>
            <div style={{ height: '100%', border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
              <Space direction='vertical' size={4}>
                <Typography.Text type='secondary'>病例级肺部状态 twin</Typography.Text>
                <Tag color={items.length > 0 && snapshots.length > 0 ? 'blue' : 'default'}>{digitalTwinSummary}</Tag>
                <Typography.Text>Shadow only / not_for_diagnosis / not formal recommendation。</Typography.Text>
              </Space>
            </div>
          </Col>
        </Row>
        <Typography.Paragraph type='secondary' style={{ marginTop: 12, marginBottom: 0 }}>
          保存影像输入元数据后，系统不会自动诊断。若后续要接入可执行路径，需要先完成课程演示级输入快照，再由受控 shadow 路径写入旁路审计；当前页面只保留入口和状态骨架。
        </Typography.Paragraph>
      </Card>
    </Space>
  );
}
