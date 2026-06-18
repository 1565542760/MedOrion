'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Button, Card, Col, Row, Space, Statistic, Tag, Typography } from 'antd';
import { getCapCopShadowWorkflowReadiness, getHealthReady, listCaseImagingInputs, listCases, listModelInputSnapshotsByCase, listPatients, type CaseItem, type PatientItem } from '@/lib/api';

function patientLabel(caseItem: CaseItem, patients: PatientItem[]) {
  const patient = patients.find((item) => item.patient_id === caseItem.patient_id);
  return patient?.display_name || patient?.external_patient_id || caseItem.patient_id;
}

export default function DashboardPage() {
  const [status, setStatus] = useState('unknown');
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [clinicalMissing, setClinicalMissing] = useState(0);
  const [imagingPending, setImagingPending] = useState(0);
  const [workflowReady, setWorkflowReady] = useState(0);
  const [failedTasks, setFailedTasks] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      const [health, caseRows, patientRows] = await Promise.allSettled([getHealthReady(), listCases(), listPatients()]);
      if (!active) return;
      setStatus(health.status === 'fulfilled' ? health.value?.status || 'unknown' : 'unknown');
      const nextCases = caseRows.status === 'fulfilled' ? caseRows.value || [] : [];
      const nextPatients = patientRows.status === 'fulfilled' ? patientRows.value || [] : [];
      setCases(nextCases);
      setPatients(nextPatients);
      const sample = nextCases.slice(0, 18);
      const summaries = await Promise.all(sample.map(async (item) => {
        const [snapshots, images, readiness] = await Promise.allSettled([
          listModelInputSnapshotsByCase(item.case_id),
          listCaseImagingInputs(item.case_id),
          getCapCopShadowWorkflowReadiness(item.case_id),
        ]);
        return {
          clinical: snapshots.status === 'fulfilled' ? snapshots.value.items.length : 0,
          imaging: images.status === 'fulfilled' ? images.value.items.length : 0,
          ready: readiness.status === 'fulfilled' && readiness.value.overall_status !== 'blocked',
          failed: readiness.status === 'rejected',
        };
      }));
      if (!active) return;
      setClinicalMissing(summaries.filter((item) => item.clinical === 0).length);
      setImagingPending(summaries.filter((item) => item.imaging === 0).length);
      setWorkflowReady(summaries.filter((item) => item.ready).length);
      setFailedTasks(summaries.filter((item) => item.failed).length);
    }
    load().catch(() => setStatus('unknown'));
    return () => { active = false; };
  }, []);

  const recentCases = useMemo(() => cases.slice(0, 5), [cases]);

  return (
    <Space direction='vertical' size={16} style={{ width: '100%', maxWidth: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <Space direction='vertical' size={2}>
          <Typography.Title level={3} style={{ margin: 0 }}>工作台</Typography.Title>
          <Typography.Text type='secondary'>今日先处理输入缺口、影像预处理和可运行的模型评估。</Typography.Text>
        </Space>
        <Space wrap>
          <Tag color={status === 'ready' ? 'green' : 'gold'}>后端：{status}</Tag>
          <Button type='primary' href='/cases'>进入患者/病例</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}><Card><Statistic title='患者/病例' value={cases.length} /></Card></Col>
        <Col xs={24} md={6}><Card><Statistic title='待补临床输入' value={clinicalMissing} /></Card></Col>
        <Col xs={24} md={6}><Card><Statistic title='待影像预处理' value={imagingPending} /></Card></Col>
        <Col xs={24} md={6}><Card><Statistic title='可进入模型评估' value={workflowReady} /></Card></Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title='最近病例' extra={<Link href='/cases'>查看全部</Link>}>
            <Space direction='vertical' size={10} style={{ width: '100%' }}>
              {recentCases.map((item) => (
                <div key={item.case_id} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, borderBottom: '1px solid #f0f0f0', paddingBottom: 10 }}>
                  <Space direction='vertical' size={0}>
                    <Typography.Text strong>{patientLabel(item, patients)}</Typography.Text>
                    <Typography.Text type='secondary'>患者ID：{item.patient_id} / 住院号：{item.case_no || '-'}</Typography.Text>
                  </Space>
                  <Button size='small' href={'/cases/' + item.case_id}>进入</Button>
                </div>
              ))}
              {recentCases.length === 0 ? <Typography.Text type='secondary'>暂无病例</Typography.Text> : null}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title='快捷入口'>
            <Space wrap>
              <Button href='/cases?status=clinical_missing'>补临床输入</Button>
              <Button href='/cases?status=imaging_pending'>处理影像</Button>
              <Button href='/cases?status=ready_for_model'>模型评估</Button>
              <Button href='/quality-reviews'>质控</Button>
              <Button href='/models'>模型管理</Button>
            </Space>
            <div style={{ marginTop: 16 }}><Tag color={failedTasks ? 'red' : 'default'}>最近失败任务：{failedTasks}</Tag></div>
          </Card>
        </Col>
      </Row>
    </Space>
  );
}
