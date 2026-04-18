import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Typography, Spin, Message, Button, Divider, Space, Avatar, Comment as ArcoComment } from '@arco-design/web-react';
import { IconThumbUp, IconMessage, IconLeft } from '@arco-design/web-react/icon';
import { PostsService } from '../../api/services/PostsService';
import { CommentsService } from '../../api/services/CommentsService';
import type { PostOut } from '../../api/models/PostOut';
import type { CommentOut } from '../../api/models/CommentOut';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const PostDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [post, setPost] = useState<PostOut | null>(null);
  const [comments, setComments] = useState<CommentOut[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    
    const fetchPostDetail = async () => {
      setLoading(true);
      try {
        const res = await PostsService.getPostPostsUserPidGet(id);
        const responseData: any = res;
        
        // 解析统一返回值结构
        if (responseData?.data && responseData.code === 200) {
          setPost(responseData.data);
        } else if (responseData?.pid) {
          setPost(responseData);
        } else {
          Message.error('无法解析帖子数据');
        }
        
        // 同时获取评论
        fetchComments(id);
      } catch (err) {
        console.error('Failed to load post detail:', err);
        Message.error('加载帖子详情失败');
      } finally {
        setLoading(false);
      }
    };

    fetchPostDetail();
  }, [id]);

  const fetchComments = async (postId: string) => {
    setCommentsLoading(true);
    try {
      const res = await CommentsService.listCommentsByPostForUserCommentsPostPostIdGet(postId, 0, 50);
      const responseData: any = res;
      
      let fetchedComments: CommentOut[] = [];
      if (responseData?.data?.items && Array.isArray(responseData.data.items)) {
        fetchedComments = responseData.data.items;
      } else if (responseData?.items && Array.isArray(responseData.items)) {
        fetchedComments = responseData.items;
      } else if (Array.isArray(responseData)) {
        fetchedComments = responseData;
      }
      
      setComments(fetchedComments);
    } catch (err) {
      console.error('Failed to load comments:', err);
      // 如果报错暂不阻断页面加载，只提示
    } finally {
      setCommentsLoading(false);
    }
  };

  if (loading) {
    return (
      <Content className="app-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Spin tip="正在加载帖子详情..." />
      </Content>
    );
  }

  if (!post) {
    return (
      <Content className="app-content">
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Title heading={3}>帖子不存在或已被删除</Title>
          <Button type="primary" onClick={() => navigate('/')}>返回首页</Button>
        </div>
      </Content>
    );
  }

  const authorId = post.author_id.substring(0, 8);

  return (
    <Content className="app-content">
      <div className="post-detail-header">
        <Button type="text" icon={<IconLeft />} onClick={() => navigate(-1)} style={{ marginBottom: '16px' }}>
          返回
        </Button>
        <Title heading={2} style={{ margin: '0 0 16px 0' }}>{post.post_content.title}</Title>
        <Space size="large" style={{ color: 'var(--color-text-3)', marginBottom: '24px' }}>
          <Space>
            <Avatar size={24}>{authorId.charAt(0).toUpperCase()}</Avatar>
            <Text type="secondary">User_{authorId}</Text>
          </Space>
          <Text type="secondary">发布于 {new Date().toLocaleDateString()}</Text>
        </Space>
      </div>

      <div className="post-detail-body" style={{ 
        fontSize: '16px', 
        lineHeight: 1.8, 
        color: 'var(--color-text-1)',
        minHeight: '200px'
      }}>
        <Paragraph>
          {post.post_content.content}
        </Paragraph>
      </div>

      <div className="post-actions" style={{ marginTop: '32px', marginBottom: '16px' }}>
        <Button type="secondary" icon={<IconThumbUp />}>
          点赞 {post.post_stats.like_count}
        </Button>
        <Button type="secondary" icon={<IconMessage />}>
          评论 {post.post_stats.comment_count}
        </Button>
      </div>

      <Divider />

      <div className="comments-section">
        <Title heading={4} style={{ marginBottom: '24px' }}>全部评论</Title>
        
        {commentsLoading ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Spin />
          </div>
        ) : comments.length > 0 ? (
          comments.map(comment => (
            <ArcoComment
              key={comment.cid}
              author={<Text style={{ fontWeight: 500 }}>User_{comment.author_id.substring(0, 8)}</Text>}
              avatar={<Avatar size={32}>{comment.author_id.charAt(0).toUpperCase()}</Avatar>}
              content={<div>{comment.comment_content.content}</div>}
              datetime={<Text type="secondary" style={{ fontSize: '12px' }}>{new Date().toLocaleString()}</Text>}
              actions={[
                <span className="action-item" key="like">
                  <IconThumbUp /> {comment.like_count || 0}
                </span>,
                <span className="action-item" key="reply">
                  <IconMessage /> 回复
                </span>
              ]}
              style={{ borderBottom: '1px solid var(--color-border-1)', paddingBottom: '16px', marginBottom: '16px' }}
            />
          ))
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-3)' }}>
            暂无评论，快来抢沙发吧~
          </div>
        )}
      </div>
    </Content>
  );
};

export default PostDetail;
