import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from '@arco-design/web-react';
import AppHeader from './components/AppHeader';
import Home from './pages/Home';

const { Footer } = Layout;

function App() {
  return (
    <BrowserRouter>
      <Layout className="app-layout">
        <AppHeader />
        
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
        
        <Footer className="app-footer">
          <div style={{ color: 'var(--color-text-3)', fontSize: '14px' }}>
            Toy Forumhub &copy; 2025 - Designed with React & Arco Design
          </div>
        </Footer>
      </Layout>
    </BrowserRouter>
  );
}

export default App;