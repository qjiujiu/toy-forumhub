from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class Post(Base):
    """ 帖子模型，对应数据库中的 posts 表。
    
        CREATE TABLE IF NOT EXISTS posts (
            pid INT AUTO_INCREMENT PRIMARY KEY,       -- 帖子 ID
            author_id INT,                            -- 作者 ID
            title VARCHAR(255) NOT NULL,              -- 帖子标题
            content TEXT NOT NULL,                    -- 帖子内容
            visibility SMALLINT DEFAULT 0,            -- 可见性（0:公开, 1:仅作者, 2:草稿）
            review_status SMALLINT DEFAULT 0,         -- 审核状态（0:待审, 1:通过, 2:拒绝）
            reviewed_at TIMESTAMP,                    -- 审核时间
            comment_count INT DEFAULT 0,              -- 评论计数
            like_count INT DEFAULT 0,                 -- 点赞计数
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
            deleted_at TIMESTAMP NULL,                -- 软删除时间戳
            FOREIGN KEY (author_id) REFERENCES users(uid)  -- 外键关联到用户表
        );
    """
    
    __tablename__ = "posts"

    pid = Column(Integer, primary_key=True, autoincrement=True)  # 帖子 ID
    author_id = Column(Integer, ForeignKey("users.uid"), nullable=False)  # 帖子作者 ID
    title = Column(String(255), nullable=False)  # 帖子标题
    content = Column(Text, nullable=False)  # 帖子内容
    visibility = Column(SmallInteger, default=0)  # 可见性（0:公开, 1:仅作者, 2:草稿）
    review_status = Column(SmallInteger, default=0)  # 审核状态（0:待审, 1:通过, 2:拒绝）
    reviewed_at = Column(TIMESTAMP, nullable=True)  # 审核时间
    comment_count = Column(Integer, default=0)  # 评论数
    like_count = Column(Integer, default=0)  # 点赞数
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)  # 创建时间
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)  # 更新时间
    deleted_at = Column(TIMESTAMP, nullable=True)  # 软删除时间戳

    # 反向引用：该帖子的所有评论
    comments = relationship("Comment", back_populates="post")
    # 反向引用：该帖子的所有点赞
    likes = relationship("Like", back_populates="post")
    # 反向引用：该帖子的作者
    author = relationship("User", back_populates="posts")