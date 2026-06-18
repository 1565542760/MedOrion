'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Card, Space, Tag, Typography } from 'antd';

const navItems = [
  { key: 'overview', label: '概览', href: (caseId: string) => '/cases/' + caseId },
  { key: 'clinical', label: '临床输入', href: (caseId: string) => '/cases/' + caseId + '/model-input' },
  { key: 'imaging', label: '影像', href: (caseId: string) => '/cases/' + caseId + '/imaging-inputs' },
  { key: 'workflow', label: '模型评估', href: (caseId: string) => '/cases/' + caseId + '/model-workflow' },
  { key: 'audit', label: '审计', href: (caseId: string) => '/cases/' + caseId + '/shadow-audit' },
  { key: 'twin', label: '数字孪生', href: (caseId: string) => '/cases/' + caseId + '/dynamic-monitoring' },
  { key: 'quality', label: '质控/反馈', href: (caseId: string) => '/cases/' + caseId + '/quality-reviews' },
];

function activeFor(pathname: string, caseId: string, href: string, key: string) {
  if (key === 'overview') return pathname === '/cases/' + caseId;
  return pathname.startsWith(href);
}

export function CaseSubNav({ caseId, patientName, patientId, caseNo }: { caseId: string; patientName?: string; patientId?: string; caseNo?: string | null }) {
  const pathname = usePathname();
  return (
    <Card bodyStyle={{ padding: 14 }} style={{ width: '100%', maxWidth: '100%', marginBottom: 16 }}>
      <Space direction='vertical' size={12} style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <Space wrap size={8}>
            <Typography.Text strong>{patientName || '患者'}</Typography.Text>
            <Tag color='blue'>患者ID：{patientId || '-'}</Tag>
            <Tag>住院/门诊号：{caseNo || '-'}</Tag>
            <Tag color='gold'>仅用于科研与辅助评估，不作为临床诊断依据</Tag>
          </Space>
          <Link href='/cases'>返回患者/病例列表</Link>
        </div>
        <Space wrap size={8}>
          {navItems.map((item) => {
            const href = item.href(caseId);
            const active = activeFor(pathname, caseId, href, item.key);
            return <Link key={item.key} href={href}><Tag color={active ? 'geekblue' : 'default'} style={{ padding: '4px 10px', cursor: 'pointer' }}>{item.label}</Tag></Link>;
          })}
        </Space>
      </Space>
    </Card>
  );
}
