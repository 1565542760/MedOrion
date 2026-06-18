'use client';

import { Card, Space, Tag, Typography } from 'antd';

export default function SettingsPage() {
  return (
    <main style={{ padding: 24, width: '100%', maxWidth: '100%', overflowX: 'hidden' }}>
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <Space direction='vertical' size={4}>
          <Typography.Title level={3} style={{ margin: 0 }}>设置</Typography.Title>
          <Typography.Text type='secondary'>系统配置、隐私模式和帮助入口会在这里集中管理。</Typography.Text>
        </Space>
        <Card title='当前设置范围'>
          <Space direction='vertical' size={8}>
            <Tag color='blue'>默认：院内医生工作站</Tag>
            <Typography.Text>主界面显示真实患者姓名、患者ID和住院/门诊号。</Typography.Text>
            <Typography.Text>科研导出、隐私模式和帮助资料后续可以从这里进入，不放在医生主流程导航中。</Typography.Text>
          </Space>
        </Card>
      </Space>
    </main>
  );
}
