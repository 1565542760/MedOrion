'use client';

import Link from 'next/link';
import { use, useEffect, useMemo, useState } from 'react';
import { Alert, Card, Descriptions, Space, Tabs, Tag, Typography } from 'antd';
import {
  getShadowRunOutputs,
  listCaseImagingInputs,
  listCases,
  listModelInputSnapshotsByCase,
  listPatients,
  listShadowRunsByCase,
  type CaseItem,
  type PatientItem,
  type ShadowInferenceRunItem,
  type ShadowInferenceRunOutputItem,
} from '@/lib/api';

type CaseContext = {
  caseItem: CaseItem | null;
  patientDisplayName: string;
  tableSnapshotCount: number;
  imagingInputCount: number;
  latestShadowRun: ShadowInferenceRunItem | null;
  latestShadowOutput: ShadowInferenceRunOutputItem | null;
  loadingError: string;
};

function pickPatientDisplayName(patient: PatientItem | undefined) {
  return patient?.display_name || patient?.external_patient_id || '-';
}

function getCaseStatusLabel(value?: string | null) {
  switch ((value || '').toLowerCase()) {
    case 'open':
      return '进行中';
    case 'closed':
      return '已关闭';
    case 'archived':
      return '已归档';
    case 'draft':
      return '草稿';
    case 'active':
      return '有效';
    default:
      return value || '-';
  }
}

function getDiseaseTaskLabel(value?: string | null) {
  if (!value) return '-';
  if (value === 'cap_cop') return 'CAP/COP';
  if (value === 'UNSPECIFIED') return '未指定';
  return value;
}

function getTwinLabel(context: CaseContext) {
  if (context.tableSnapshotCount === 0 && context.imagingInputCount === 0) return '数字孪生待建立';
  if (context.tableSnapshotCount > 0 && context.imagingInputCount === 0) return '表格先行 / 影像待补齐';
  if (context.tableSnapshotCount === 0 && context.imagingInputCount > 0) return '影像已登记 / 表格待补齐';
  if (context.latestShadowRun) return '病例级肺部状态 twin 可查看';
  return '病例级肺部状态 twin 待接入';
}

export default function CaseWorkbenchPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [context, setContext] = useState<CaseContext>({
    caseItem: null,
    patientDisplayName: '-',
    tableSnapshotCount: 0,
    imagingInputCount: 0,
    latestShadowRun: null,
    latestShadowOutput: null,
    loadingError: '',
  });
  const [loading, setLoading] = useState(true);

  const latestShadowRunId = context.latestShadowRun?.shadow_run_id || '';
  const latestShadowCandidate = context.latestShadowOutput?.candidate_label || '';
  const loadingBanner = loading ? (
    <Alert type='info' showIcon message='病例工作台加载中' description='正在汇总表格输入、影像输入和 Shadow 状态。' />
  ) : null;

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [casesResult, patientsResult, snapshotResult, imagingResult, shadowResult] = await Promise.allSettled([
          listCases(),
          listPatients(),
          listModelInputSnapshotsByCase(caseId),
          listCaseImagingInputs(caseId),
          listShadowRunsByCase(caseId),
        ]);

        if (!active) return;

        const caseItem = casesResult.status === 'fulfilled'
          ? (casesResult.value || []).find((item) => item.case_id === caseId) || null
          : null;
        const patientMap = patientsResult.status === 'fulfilled'
          ? new Map(patientsResult.value.map((item) => [item.patient_id, pickPatientDisplayName(item)]))
          : new Map<string, string>();
        const snapshots = snapshotResult.status === 'fulfilled' ? snapshotResult.value.items || [] : [];
        const imagingInputs = imagingResult.status === 'fulfilled' ? imagingResult.value.items || [] : [];
        const shadowRuns = shadowResult.status === 'fulfilled' ? shadowResult.value.items || [] : [];
        const latestShadowRun = [...shadowRuns].sort(
          (a, b) => new Date(b.started_at || b.created_at || 0).getTime() - new Date(a.started_at || a.created_at || 0).getTime(),
        )[0] || null;
        const latestShadowOutput = latestShadowRun
          ? (await getShadowRunOutputs(latestShadowRun.shadow_run_id).catch(() => ({ items: [] as ShadowInferenceRunOutputItem[], total: 0 }))).items?.[0] || null
          : null;

        setContext({
          caseItem,
          patientDisplayName: caseItem ? (patientMap.get(caseItem.patient_id) || '-') : '-',
          tableSnapshotCount: snapshots.length,
          imagingInputCount: imagingInputs.length,
          latestShadowRun,
          latestShadowOutput,
          loadingError: '',
        });
      } catch {
        if (!active) return;
        setContext((current) => ({ ...current, loadingError: '病例工作台加载失败，请确认后端服务和登录状态。' }));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [caseId]);

  const headerSummary = useMemo(() => [
    { label: '患者姓名 / 显示名', value: context.patientDisplayName || '-' },
    { label: '病例编号', value: context.caseItem?.case_no || '-' },
    { label: '病种任务', value: getDiseaseTaskLabel(context.caseItem?.disease_task) },
    { label: '当前病例状态', value: getCaseStatusLabel(context.caseItem?.status) },
  ], [context.caseItem, context.patientDisplayName]);

  const overviewCards = [
    {
      title: '表格输入状态',
      badge: context.tableSnapshotCount > 0 ? '已登记' : '待补齐',
      description: context.tableSnapshotCount > 0 ? '已有表格输入快照，可继续做模型预览和 shadow 审计。' : '请先进入“输入数据”补齐表格特征与输入快照。',
    },
    {
      title: '影像输入状态',
      badge: context.imagingInputCount > 0 ? '已登记' : '待登记',
      description: context.imagingInputCount > 0 ? '已有影像 metadata / reference 登记。' : '请先进入“输入数据”登记影像输入 / 引用。',
    },
    {
      title: 'clinical MLP shadow 状态',
      badge: context.latestShadowRun ? '旁路已完成' : 'schema_unverified / 待接入',
      description: context.latestShadowRun
        ? ('结果只用于 shadow 审计和医生复核，不能当作诊断或正式推荐。' + (latestShadowCandidate ? ' 当前候选标签：' + latestShadowCandidate + '。' : ''))
        : '当前仍是 tabular baseline，schema_unverified 风险仍需保留。',
    },
    {
      title: 'imaging ResNet18 shadow 状态',
      badge: '原型候选 / 未执行',
      description: '当前只有 artifact preflight 和 runner prototype candidate，前端不把它包装成真实结果。',
    },
    {
      title: 'multimodal ResNet18 shadow 状态',
      badge: '待接入',
      description: '多模态融合入口先保留位置，不在本阶段触发任何运行。',
    },
    {
      title: '数字孪生状态',
      badge: getTwinLabel(context),
      description: '病例级 lung-state twin 只用于课程演示与审计展示，不是诊断图。',
    },
  ];

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Card size='small' style={{ width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
        <Space direction='vertical' size={8} style={{ width: '100%' }}>
          <Space wrap size={8}>
            <Typography.Title level={4} style={{ margin: 0 }}>病例工作台</Typography.Title>
            <Tag color='blue'>Shadow only</Tag>
            <Tag color='gold'>非诊断</Tag>
            <Tag color='gold'>非正式推荐</Tag>
          </Space>
          <Descriptions bordered size='small' column={2}>
            {headerSummary.map((item) => (
              <Descriptions.Item key={item.label} label={item.label}>
                {item.value}
              </Descriptions.Item>
            ))}
          </Descriptions>
          <Typography.Text type='secondary'>
            这里是病例总工作台，所有模块都从这一层进入，不再一层套一层。
          </Typography.Text>
        </Space>
      </Card>

      {context.loadingError ? <Alert type='error' showIcon message={context.loadingError} /> : null}
      {loadingBanner}

      <Tabs
        destroyInactiveTabPane={false}
        items={[
          {
            key: 'overview',
            label: '总览',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Typography.Text type='secondary'>按医生工作流把病例状态收拢在一层里看，不把技术状态直接堆成主视觉。</Typography.Text>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, width: '100%' }}>
                  {overviewCards.map((item) => (
                    <div key={item.title} style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                      <Space direction='vertical' size={4}>
                        <Typography.Text type='secondary'>{item.title}</Typography.Text>
                        <Tag color='blue'>{item.badge}</Tag>
                        <Typography.Text>{item.description}</Typography.Text>
                      </Space>
                    </div>
                  ))}
                </div>
              </Space>
            ),
          },
          {
            key: 'inputs',
            label: '输入数据',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='info'
                  showIcon
                  message='输入数据分层管理'
                  description='表格特征与输入快照、影像输入 / 引用登记、缺失值确认都在这里汇总。先看输入，再谈模型评估。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>表格特征与输入快照</Typography.Text>
                      <Tag color={context.tableSnapshotCount > 0 ? 'green' : 'default'}>{context.tableSnapshotCount > 0 ? '已登记' : '待补齐'}</Tag>
                      <Typography.Text>CAP/COP 临床特征在这里查看输入映射和校验状态。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/model-input'}>进入表格输入</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>影像输入 / 引用登记</Typography.Text>
                      <Tag color={context.imagingInputCount > 0 ? 'green' : 'default'}>{context.imagingInputCount > 0 ? '已登记' : '待登记'}</Tag>
                      <Typography.Text>只登记影像 metadata / reference，不上传文件，不触发模型。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/imaging-inputs'}>进入影像输入</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>缺失值确认</Typography.Text>
                      <Tag color='gold'>需要医生确认</Tag>
                      <Typography.Text>遇到 required feature 缺失时，走缺失值咨询或明确默认策略，不能 silent fallback。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/missing-consultation'}>进入缺失值确认</Link>
                    </Space>
                  </div>
                </div>
              </Space>
            ),
          },
          {
            key: 'models',
            label: '模型评估',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='warning'
                  showIcon
                  message='这里展示的是 shadow only 状态，不是诊断结论'
                  description='clinical MLP 仍保留 schema_unverified 风险；imaging ResNet18 仍是 prototype candidate；multimodal 还未接入。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>clinical MLP</Typography.Text>
                      <Space wrap size={6}>
                        <Tag color='orange'>tabular baseline</Tag>
                        <Tag color='orange'>schema_unverified</Tag>
                        <Tag>Shadow only</Tag>
                      </Space>
                      <Typography.Text>只用于 shadow 审计和医生复核，不要当作正式推荐。</Typography.Text>
                      {context.latestShadowRun
                        ? <Link href={'/cases/' + caseId + '/shadow-audit?shadow_run_id=' + latestShadowRunId}>查看临床 MLP 审计</Link>
                        : <Link href={'/cases/' + caseId + '/shadow-audit'}>查看 Shadow 审计</Link>}
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>imaging ResNet18</Typography.Text>
                      <Space wrap size={6}>
                        <Tag color='gold'>artifact preflight</Tag>
                        <Tag color='gold'>runner prototype candidate</Tag>
                        <Tag>backend bridge stub</Tag>
                      </Space>
                      <Typography.Text>当前只保留原型与桥接位置，不把它包装成真实结果。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/imaging-inputs'}>查看影像输入</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>multimodal ResNet18</Typography.Text>
                      <Space wrap size={6}>
                        <Tag color='default'>待接入</Tag>
                        <Tag>Shadow only</Tag>
                      </Space>
                      <Typography.Text>多模态融合先保留位置，不在本阶段触发任何执行。</Typography.Text>
                    </Space>
                  </div>
                </div>
              </Space>
            ),
          },
          {
            key: 'twin',
            label: '数字孪生',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='info'
                  showIcon
                  message='病例级 lung-state twin 仅用于课程演示'
                  description='它显示输入状态、影像状态、模型状态和不确定性 / 限制，不是诊断图，也不是正式临床推荐。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>输入状态</Typography.Text>
                      <Typography.Text>{context.tableSnapshotCount > 0 ? '表格输入快照已建立' : '表格输入待建立'}</Typography.Text>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>影像状态</Typography.Text>
                      <Typography.Text>{context.imagingInputCount > 0 ? '影像 metadata / reference 已登记' : '影像输入待登记'}</Typography.Text>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>模型状态</Typography.Text>
                      <Typography.Text>{context.latestShadowRun ? '已有 Shadow 记录' : '仍是 Shadow only / prototype'}</Typography.Text>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={4}>
                      <Typography.Text type='secondary'>不确定性 / 限制</Typography.Text>
                      <Typography.Text>
                        {context.latestShadowOutput
                          ? '概率未校准、仅供复核'
                          : '当前仍是课程演示，不可当诊断'}
                      </Typography.Text>
                    </Space>
                  </div>
                </div>
                <Alert
                  type='warning'
                  showIcon
                  message='课程演示标识'
                  description='Shadow only / not_for_diagnosis / not formal recommendation。病例级肺部状态 twin 只保留展示，不产生诊断结论。'
                />
              </Space>
            ),
          },
          {
            key: 'audit',
            label: '审计溯源',
            children: (
              <Space direction='vertical' size={12} style={{ width: '100%' }}>
                <Alert
                  type='info'
                  showIcon
                  message='审计与溯源入口收口'
                  description='这里汇总 Shadow 审计、Trace / provenance 和访问审计的入口。技术字段只在详情或折叠区展示。'
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, width: '100%' }}>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>Shadow 审计</Typography.Text>
                      <Typography.Text>查看旁路审计记录、候选标签和输出摘要。</Typography.Text>
                      <Link href={latestShadowRunId ? '/cases/' + caseId + '/shadow-audit?shadow_run_id=' + latestShadowRunId : '/cases/' + caseId + '/shadow-audit'}>进入 Shadow 审计</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>Trace / provenance</Typography.Text>
                      <Typography.Text>查看病例溯源与证据链入口，但不把 raw JSON 作为主视觉。</Typography.Text>
                      <Link href={'/cases/' + caseId + '/lineage'}>进入 Trace / 溯源</Link>
                    </Space>
                  </div>
                  <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fff' }}>
                    <Space direction='vertical' size={6}>
                      <Typography.Text type='secondary'>Access audit</Typography.Text>
                      <Typography.Text>前端暂只保留工作台入口位，实际访问审计待接入。</Typography.Text>
                      <Tag>待接入</Tag>
                    </Space>
                  </div>
                </div>
              </Space>
            ),
          },
        ]}
      />
    </Space>
  );
}
