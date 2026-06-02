'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Button, Card, Col, Row, Space, Statistic, Tag, Typography } from 'antd';
import { getHealthReady } from '@/lib/api';
import RiskTrendPlaceholder from '@/components/RiskTrendPlaceholder';

export default function DashboardPage() {
  const [status, setStatus] = useState('unknown');

  useEffect(() => {
    getHealthReady().then((data) => setStatus(data?.status || 'unknown')).catch(() => setStatus('unknown'));
  }, []);

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Card>
        <Space>
          <Typography.Text strong>系统状态</Typography.Text>
          <Tag color={status === 'ready' ? 'green' : 'gold'}>{status}</Tag>
        </Space>
      </Card>
      <Row gutter={16}>
        <Col span={8}><Card><Statistic title='待处理病例' value={18} /></Card></Col>
        <Col span={8}><Card><Statistic title='缺失值待确认' value={7} /></Card></Col>
        <Col span={8}><Card><Statistic title='高风险提示' value={3} /></Card></Col>
      </Row>
      <Card title='风险趋势占位图'><RiskTrendPlaceholder /></Card>
      <Card title='快速入口'>
        <Space wrap>
          <Button><Link href='/cases'>病例列表</Link></Button>
          <Button><Link href='/cases/case-001/missing-consultation'>缺失值咨询</Link></Button>
          <Button><Link href='/cases/case-001/small-models'>小模型结果</Link></Button>
          <Button><Link href='/cases/case-001/llm-explanation'>LLM解释</Link></Button>
          <Button><Link href='/cases/case-001/lineage'>查看溯源与证据链</Link></Button>
          <Button><Link href='/cases/case-001/feedback'>医生反馈</Link></Button>
        </Space>
      </Card>
    </Space>
  );
}
