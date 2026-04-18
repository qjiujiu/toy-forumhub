import React, { useState } from 'react';
import { Layout, Typography, Form, Input, Button, Message, Space, Link } from '@arco-design/web-react';
import { useNavigate } from 'react-router-dom';
import { IconUser, IconLock } from '@arco-design/web-react/icon';

const { Content } = Layout;
const { Title, Text } = Typography;
const FormItem = Form.Item;

const Login: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // 模拟登录请求，后续可以替换为真实的 API 调用
      console.log('Login values:', values);
      await new Promise(resolve => setTimeout(resolve, 800));
      Message.success('登录成功');
      navigate('/');
    } catch (err) {
      Message.error('登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Content className="app-content auth-content">
      <div className="auth-container">
        <div className="auth-header">
          <Title heading={3}>登录</Title>
          <Text type="secondary">欢迎回到 Toy Forumhub</Text>
        </div>
        
        <Form form={form} layout="vertical" onSubmit={handleSubmit} className="auth-form">
          <FormItem field="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<IconUser />} placeholder="用户名" size="large" />
          </FormItem>
          
          <FormItem field="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<IconLock />} placeholder="密码" size="large" />
          </FormItem>
          
          <FormItem>
            <Button type="primary" htmlType="submit" long size="large" loading={loading}>
              登录
            </Button>
          </FormItem>
        </Form>
        
        <div className="auth-footer">
          <Space>
            <Text type="secondary">还没有账号？</Text>
            <Link onClick={() => navigate('/register')}>立即注册</Link>
          </Space>
        </div>
      </div>
    </Content>
  );
};

export default Login;
