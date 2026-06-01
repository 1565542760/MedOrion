'use client';

import { Card, Space, Table, Tag, Typography } from 'antd';

const rows = [
  { model_name: 'cap-risk-model', version: 'v0.3.1', status: 'active' },
  { model_name: 'cop-severity-model', version: 'v0.2.4', status: 'staged' }
];

export default function Page() {
  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>模型管理与版本管理</Typography.Title>
      <Card>
        <Table
          rowKey='model_name'
          dataSource={rows}
          pagination={false}
          columns={[
            { title: 'Model', dataIndex: 'model_name' },
            { title: 'Version', dataIndex: 'version' },
            { title: 'Status', dataIndex: 'status', render: (v: string) => <Tag>{v}</Tag> }
          ]}
        />
      </Card>
    </Space>
  );
}
