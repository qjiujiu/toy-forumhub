import { Layout, Button, Typography } from '@arco-design/web-react';
import React from 'react';

const { Header } = Layout;
const { Title } = Typography;

const AppHeader: React.FC = () => {
  return (
    <Header className="app-header">
      <div className="app-header-inner">
        <div className="logo">
          <span className="app-title">Toy Forumhub</span>
        </div>
        <div className="actions">
          <Button type="secondary">登录</Button>
          <Button type="primary">注册</Button>
        </div>
      </div>
    </Header>
  );
};

export default AppHeader;
