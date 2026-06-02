'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Alert, Button, Card, Form, Input, Space, Typography } from 'antd';
import { useAuth } from '@/components/AuthProvider';

type ApiError = {
  response?: {
    data?: {
      detail?: {
        code?: string;
      };
    };
  };
};

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, router]);

  async function onFinish(values: { username: string; password: string }) {
    setSubmitting(true);
    setError('');
    try {
      await login(values.username, values.password);
      router.replace('/dashboard');
    } catch (e: unknown) {
      const code = (e as ApiError)?.response?.data?.detail?.code;
      if (code === 'invalid_credentials') {
        setError('登录失败：用户名或密码错误');
      } else if (code === 'auth_storage_not_ready') {
        setError('登录失败：认证服务暂不可用');
      } else {
        setError('登录失败：请稍后重试');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <Card style={{ width: 420 }}>
        <Space direction='vertical' size={16} style={{ width: '100%' }}>
          <Typography.Title level={4} style={{ margin: 0 }}>登录</Typography.Title>
          <Typography.Text type='secondary'>开发环境最小登录入口（非生产公网登录）。</Typography.Text>
          {error ? <Alert type='error' showIcon message={error} /> : null}
          <Form layout='vertical' onFinish={onFinish}>
            <Form.Item label='用户名' name='username' rules={[{ required: true, message: '请输入用户名' }]}>
              <Input autoComplete='username' />
            </Form.Item>
            <Form.Item label='密码' name='password' rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password autoComplete='current-password' />
            </Form.Item>
            <Button type='primary' htmlType='submit' loading={submitting} block>登录</Button>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
