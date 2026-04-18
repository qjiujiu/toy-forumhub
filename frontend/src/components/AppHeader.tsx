import { Layout, Button, Typography } from '@arco-design/web-react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

const { Header } = Layout;
const { Title } = Typography;

const AppHeader: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Header className="app-header">
      <div className="app-header-inner">
        <div className="logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <span className="app-title">Toy Forumhub</span>
        </div>
        <div className="actions">
          <Button type="secondary" onClick={() => navigate('/login')}>登录</Button>
          <Button type="primary" onClick={() => navigate('/register')}>注册</Button>
        </div>
      </div>
    </Header>
  );
};

export default AppHeader;
