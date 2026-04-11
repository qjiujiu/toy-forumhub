import React, { useEffect, useState } from 'react';
import { Layout, Button, Spin, Empty, Typography, Message } from '@arco-design/web-react';
import { PostsService } from '../api/services/PostsService';
import { OpenAPI } from '../api/core/OpenAPI';
import type { PostOut } from '../api/models/PostOut';
import PostCard from '../components/PostCard';

const { Content } = Layout;
const { Title } = Typography;

OpenAPI.BASE = 'http://127.0.0.1:8000';

const Home: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [posts, setPosts] = useState<PostOut[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await PostsService.listPostsPostsGet(0, 10);
      const responseData: any = res;
      
      // Handle wrapper from BizResponse or direct array
      let fetchedPosts: PostOut[] = [];
      if (responseData?.data?.items && Array.isArray(responseData.data.items)) {
        fetchedPosts = responseData.data.items;
      } else if (responseData?.items && Array.isArray(responseData.items)) {
        fetchedPosts = responseData.items;
      }
      
      setPosts(fetchedPosts);
    } catch (err) {
      console.error(err);
      Message.error('加载帖子列表失败或网络错误');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <Content className="app-content">
      <div className="content-header">
        <Title heading={2} style={{ margin: 0 }}>最新帖子</Title>
        <Button onClick={loadData} loading={loading}>刷新帖子</Button>
      </div>

      {loading && posts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin tip="数据加载中..." />
        </div>
      ) : posts.length === 0 ? (
        <Empty description="暂无帖子数据" style={{ padding: '60px 0' }} />
      ) : (
        <div className="post-list">
          {posts.map(post => (
            <PostCard key={post.pid} post={post} />
          ))}
        </div>
      )}
    </Content>
  );
};

export default Home;
