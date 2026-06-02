import type { Metadata } from 'next';
import 'antd/dist/reset.css';
import './globals.css';
import AppShell from '@/components/AppShell';
import { AuthProvider } from '@/components/AuthProvider';

export const metadata: Metadata = {
  title: 'MedOrion Frontend',
  description: 'Doctor workstation stage 19'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang='zh-CN'><body><AuthProvider><AppShell>{children}</AppShell></AuthProvider></body></html>;
}
