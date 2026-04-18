import React, { useState } from 'react';
import { Layout, Typography, Form, Input, Button, Message, Space, Link } from '@arco-design/web-react';
import { useNavigate } from 'react-router-dom';
import { IconUser, IconLock } from '@arco-design/web-react/icon';

const { Content } = Layout;
const { Title, Text } = Typography;
const FormItem = Form.Item;

const Register: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      if (values.password !== values.confirmPassword) {
        Message.error('两次输入的密码不一致');
        return;
      }
      
      // 模拟注册请求
      console.log('Register values:', values);
      await new Promise(resolve => setTimeout(resolve, 800));
      Message.success('注册成功，请登录');
      navigate('/login');
    } catch (err) {
      Message.error('注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Content className="app-content auth-content">
      <div className="auth-container">
        <div className="auth-header">
          <Title heading={3}>注册</Title>
          <Text type="secondary">加入 Toy Forumhub 社区</Text>
        </div>
        
        <Form form={form} layout="vertical" onSubmit={handleSubmit} className="auth-form">
          <FormItem field="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<IconUser />} placeholder="用户名" size="large" />
          </FormItem>
          
          <FormItem field="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<IconLock />} placeholder="密码" size="large" />
          </FormItem>
          
          <FormItem 
            field="confirmPassword" 
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              {
                validator: (v, cb) => {
                  if (!v || form.getFieldValue('password') === v) {
                    cb();
                  } else {
                    cb('两次输入的密码不一致');
                  }
                }
              }
            ]}
          >
            <Input.Password prefix={<IconLock />} placeholder="确认密码" size="large" />
          </FormItem>
          
          <FormItem>
            <Button type="primary" htmlType="submit" long size="large" loading={loading}>
              注册
            </Button>
          </FormItem>
        </Form>
        
        <div className="auth-footer">
          <Space>
            <Text type="secondary">已有账号？</Text>
            <Link onClick={() => navigate('/login')}>立即登录</Link>
          </Space>
        </div>
      </div>
    </Content>
  );
};

export default Register;
