'use client';

import { use } from 'react';
import { Card, Col, Row, Space, Typography } from 'antd';

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return <Space direction='vertical' size={16} style={{ width: '100%' }}><Typography.Title level={4} style={{ margin: 0 }}>多模态数据查看</Typography.Title><Typography.Text type='secondary'>Case: {caseId}</Typography.Text><Row gutter={16}><Col span={12}><Card title='结构化数据'>检验、生命体征、评分表占位</Card></Col><Col span={12}><Card title='文本数据'>病程记录、医嘱、入院记录占位</Card></Col></Row><Card title='影像区（Cornerstone 预留）'>后续接入 Cornerstone。</Card></Space>;
}
