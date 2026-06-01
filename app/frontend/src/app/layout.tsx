import type { Metadata } from 'next';
import 'antd/dist/reset.css';
import './globals.css';
import AppShell from '@/components/AppShell';

export const metadata: Metadata = {
  title: 'MedOrion Frontend',
  description: 'Doctor workstation stage 01'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang='zh-CN'><body><AppShell>{children}</AppShell></body></html>;
}
