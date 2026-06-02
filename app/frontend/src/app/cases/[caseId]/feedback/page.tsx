'use client';

import { use } from 'react';
import { Button, Card, Form, Input, Select, Space, Typography } from 'antd';

export default function Page({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return <Space direction='vertical' size={16} style={{ width: '100%' }}><Typography.Title level={4} style={{ margin: 0 }}>医生反馈</Typography.Title><Typography.Text type='secondary'>病例：{caseId}</Typography.Text><Card><Form layout='vertical'><Form.Item label='反馈类型'><Select options={[{ label: '证据不足', value: 'evidence_gap' }, { label: '建议不一致', value: 'recommendation_conflict' }, { label: '其他', value: 'other' }]} /></Form.Item><Form.Item label='反馈内容'><Input.TextArea rows={4} /></Form.Item><Button type='primary'>提交（占位）</Button></Form></Card></Space>;
}
