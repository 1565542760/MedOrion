'use client';

import type { ReactNode } from 'react';
import { Card, Space, Typography } from 'antd';

export function WorkspaceTableShell({
  title,
  subtitle,
  actions,
  children,
  minHeight = 480,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  minHeight?: number;
}) {
  return (
    <Card
      bodyStyle={{ padding: 0, overflow: 'hidden' }}
      title={
        <Space direction='vertical' size={0} style={{ minWidth: 0 }}>
          <Typography.Text strong>{title}</Typography.Text>
          {subtitle ? <Typography.Text type='secondary' style={{ fontSize: 12 }}>{subtitle}</Typography.Text> : null}
        </Space>
      }
      extra={actions}
      style={{ width: '100%', maxWidth: '100%' }}
    >
      <div
        className='workspace-table-window'
        style={{
          minHeight,
          maxHeight: 'calc(100vh - 260px)',
          overflow: 'auto',
          width: '100%',
          maxWidth: '100%',
        }}
      >
        {children}
      </div>
    </Card>
  );
}

export function PageSection({ title, subtitle, actions, children }: { title: string; subtitle?: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section style={{ width: '100%', maxWidth: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', marginBottom: 12 }}>
        <Space direction='vertical' size={2} style={{ minWidth: 0 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>{title}</Typography.Title>
          {subtitle ? <Typography.Text type='secondary'>{subtitle}</Typography.Text> : null}
        </Space>
        {actions}
      </div>
      {children}
    </section>
  );
}
