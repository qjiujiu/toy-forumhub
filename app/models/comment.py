from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base


class Comment(Base):
    """ 评论模型，对应数据库中的 comments 表。
    
        CREATE TABLE IF NOT EXISTS comments (
            cid INT AUTO_INCREMENT PRIMARY KEY,         -- 评论 ID
            post_id INT,                                -- 帖子 ID
            author_id INT,                              -- 评论作者 ID
            parent_id INT,                              -- 父评论 ID (楼中楼)
            root_id INT,                                -- 顶级评论 ID
            content TEXT NOT NULL,                      -- 评论内容
            like_count INT DEFAULT 0,                   -- 点赞数
            status SMALLINT DEFAULT 0,                  -- 评论状态（0:正常, 1:折叠）
            review_status SMALLINT DEFAULT 0,           -- 审核状态（0:待审, 1:通过, 2:拒绝）
            reviewed_at TIMESTAMP,                      -- 审核时间
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
            deleted_at TIMESTAMP NULL,                  -- 软删除时间戳
            FOREIGN KEY (post_id) REFERENCES posts(pid),    -- 外键关联到帖子表
            FOREIGN KEY (author_id) REFERENCES users(uid),  -- 外键关联到用户表
            FOREIGN KEY (parent_id) REFERENCES comments(cid) -- 外键关联到评论表（楼中楼）
        );
    """
    
    __tablename__ = "comments"

    cid = Column(Integer, primary_key=True, autoincrement=True)  # 评论 ID
    post_id = Column(Integer, ForeignKey("posts.pid"), nullable=False)  # 帖子 ID
    author_id = Column(Integer, ForeignKey("users.uid"), nullable=False)  # 评论作者 ID
    parent_id = Column(Integer, ForeignKey("comments.cid"), nullable=True)  # 父评论 ID（楼中楼）
    root_id = Column(Integer, nullable=False)  # 顶级评论 ID
    content = Column(Text, nullable=False)  # 评论内容
    like_count = Column(Integer, default=0)  # 点赞数
    status = Column(SmallInteger, default=0)  # 评论状态（0:正常, 1:折叠）
    review_status = Column(SmallInteger, default=0)  # 审核状态（0:待审, 1:通过, 2:拒绝）
    reviewed_at = Column(TIMESTAMP, nullable=True)  # 审核时间
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)  # 创建时间
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)  # 更新时间
    deleted_at = Column(TIMESTAMP, nullable=True)  # 软删除时间戳

    # 反向引用：该评论的帖子
    post = relationship("Post", back_populates="comments")
    # 反向引用：该评论的作者
    author = relationship("User", back_populates="comments")
    # 反向引用：该评论的父评论（楼中楼）
    parent = relationship("Comment", back_populates="child", remote_side=[cid])
    # 反向引用：该评论的子评论（楼中楼）
    child = relationship("Comment", back_populates="parent")