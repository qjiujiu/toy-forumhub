from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base
from enum import Enum as PyEnum          # Python 原生枚举
from sqlalchemy import Enum as SAEnum    # SQLAlchemy 数据类型
import uuid

# 帖子可见性
class PostVisibility(PyEnum):
    PUBLIC = 0  # 公开
    AUTHOR_ONLY = 1  # 仅作者
    DRAFT = 2  # 草稿

# 帖子审核状态
class PostReviewStatus(PyEnum):
    PENDING = 0  # 待审
    APPROVED = 1  # 通过
    REJECTED = 2  # 拒绝

class Post(Base):
    """ 帖子模型，对应数据库中的 posts 表。
    
        CREATE TABLE IF NOT EXISTS posts (
            id INT AUTO_INCREMENT PRIMARY KEY,           -- 系统主键ID（自增）
            pid VARCHAR(36) UNIQUE,                      -- 业务主键PID（UUID）
            author_id VARCHAR(36) NOT NULL,              -- 作者 ID
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
        -- 为 author_id 添加索引，以便快速查询某个作者的帖子
        CREATE INDEX idx_posts_author_id ON posts (author_id);

        -- 为 visibility 和 review_status 添加联合索引，以便快速筛选帖子
        CREATE INDEX idx_posts_visibility_review_status ON posts (visibility, review_status);

        -- 可选择联合索引，查询特定作者和可见性（如公开、草稿等）的帖子
        CREATE INDEX idx_posts_author_visibility ON posts (author_id, visibility);
    """
    
    __tablename__ = "posts"

    # 系统主键：自增
    id = Column(Integer, primary_key=True, autoincrement=True)  # 系统主键ID，系统用，不对外暴露
    # 业务主键：UUID，唯一且不自增
    pid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))  # 用户的业务主键（UUID形式）

    author_id = Column(String(36), ForeignKey("users.uid"), nullable=False)  # 帖子作者 ID
    title = Column(String(255), nullable=False)  # 帖子标题
    content = Column(Text, nullable=False)  # 帖子内容
    visibility = Column(SAEnum(PostVisibility), default=PostVisibility.PUBLIC)  # 可见性（0:公开, 1:仅作者, 2:草稿）
    review_status = Column(SAEnum(PostReviewStatus), default=PostReviewStatus.PENDING)  # 审核状态（0:待审, 1:通过, 2:拒绝）
    reviewed_at = Column(TIMESTAMP, nullable=True)  # 审核时间
    comment_count = Column(Integer, default=0)  # 评论数
    like_count = Column(Integer, default=0, nullable=False)  # 点赞数
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)  # 创建时间
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)  # 更新时间
    deleted_at = Column(TIMESTAMP, nullable=True)  # 软删除时间戳

    # 反向引用：该帖子的所有评论
    comments = relationship("Comment", back_populates="post")
    # 反向引用：该帖子的所有点赞
    likes = relationship("Like", back_populates="post")
    # 反向引用：该帖子的作者
    author = relationship("User", back_populates="posts")

    __table_args__ = (
        # 保证业务主键 pid 唯一
        UniqueConstraint('pid', name='unique_pid'),
        # 单列索引
        Index("idx_posts_author_id", "author_id"),
        # 联合索引
        Index("idx_posts_visibility_review_status", "visibility", "review_status"),
        Index("idx_posts_author_visibility", "author_id", "visibility"),
    )