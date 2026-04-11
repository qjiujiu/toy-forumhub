import React from 'react';
import { Card, Typography, Space } from '@arco-design/web-react';
import { IconThumbUp, IconMessage } from '@arco-design/web-react/icon';
import { PostOut } from '../api/models/PostOut';

const { Text } = Typography;

interface PostCardProps {
  post: PostOut;
}

const PostCard: React.FC<PostCardProps> = ({ post }) => {
  const { title, content } = post.post_content;
  const { like_count, comment_count } = post.post_stats;
  const authorId = post.author_id.substring(0, 8);

  return (
    <Card 
      title={title} 
      hoverable 
      className="post-card"
      bordered
    >
      <div className="post-card-meta">
        <Text type="secondary">作者: User_{authorId}</Text>
      </div>
      
      <div className="post-card-body" style={{ minHeight: '60px', color: 'var(--color-text-2)'}}>
        {content}
      </div>

      <div className="post-actions">
        <span className="action-item">
          <IconThumbUp /> {like_count}
        </span>
        <span className="action-item">
          <IconMessage /> {comment_count}
        </span>
      </div>
    </Card>
  );
};

export default PostCard;
