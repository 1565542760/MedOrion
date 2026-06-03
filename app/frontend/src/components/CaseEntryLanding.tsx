"use client";

import { Alert, Button, Card, Space, Tag, Typography } from 'antd';

type Props = {
  title: string;
  subtitle: string;
  note: string;
  bullets: string[];
};

export default function CaseEntryLanding({ title, subtitle, note, bullets }: Props) {
  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>{title}</Typography.Title>
      <Alert type='info' showIcon message={subtitle} description={note} />
      <Card title={'\u4f7f\u7528\u8bf4\u660e'}>
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Space wrap>
            <Tag color='blue'>{'\u5148\u9009\u75c5\u4f8b'}</Tag>
            <Tag color='geekblue'>{'\u75c5\u4f8b\u7ea7\u5de5\u4f5c\u6d41'}</Tag>
            <Tag color='cyan'>{'\u767b\u5f55\u540e\u53ef\u8bbf\u95ee'}</Tag>
          </Space>
          <ul style={{ margin: 0, paddingInlineStart: 20 }}>
            {bullets.map((item) => <li key={item} style={{ marginBottom: 8 }}>{item}</li>)}
          </ul>
          <Space wrap>
            <Button type='primary' href='/cases'>{'\u53bb\u75c5\u4f8b\u5217\u8868'}</Button>
            <Button href='/dashboard'>{'\u56de\u5de5\u4f5c\u53f0'}</Button>
          </Space>
        </Space>
      </Card>
    </Space>
  );
}
