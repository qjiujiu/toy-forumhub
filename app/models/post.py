from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base
import uuid
from enum import IntEnum  
# 帖子可见性
class PostVisibility(IntEnum):
    PUBLIC = 0        # 所有人可见
    AUTHOR_ONLY = 1   # 仅作者可见
    # 以后可以扩展：
    # FOLLOWERS_ONLY = 2
    # MUTUAL_ONLY = 3

# 帖子的发布状态
class PostPublishStatus(IntEnum):
    DRAFT = 0         # 草稿（未发布）
    PUBLISHED = 1     # 已发布

# 帖子审核状态
class PostReviewStatus(IntEnum):
    PENDING = 0   # 待审
    APPROVED = 1  # 通过
    REJECTED = 2  # 拒绝

class Post(Base):
    """ 帖子动态表，存储帖子的状态、点赞数、评论数等动态信息。

        CREATE TABLE IF NOT EXISTS posts (
            _id INT AUTO_INCREMENT PRIMARY KEY,           -- 系统主键ID（自增）
            pid VARCHAR(36) UNIQUE,                       -- 业务主键PID（UUID）
            author_id VARCHAR(36) NOT NULL,               -- 作者 ID (Fk->users.uid)
            visibility SMALLINT DEFAULT 0,                -- 可见性（0:公开, 1:仅作者）
            publish_status SMALLINT DEFAULT 1,            -- 发布状态（0:草稿, 1:发布）
            review_status SMALLINT DEFAULT 0,             -- 审核状态（0:待审, 1:通过, 2:拒绝）
            reviewed_at TIMESTAMP,                        -- 审核时间
            deleted_at TIMESTAMP NULL,                    -- 软删除时间戳

            FOREIGN KEY (author_id) REFERENCES users(uid)   -- 外键关联到用户表
        );

        -- 索引建议：
        -- 1) 为 author_id 添加索引，以便快速查询某个作者的帖子
        CREATE INDEX idx_posts_author_id ON posts (author_id);

        -- 2) 为 visibility 和 review_status 添加联合索引，以便快速筛选帖子
        CREATE INDEX idx_posts_visibility_review_status ON posts (visibility, review_status);

        -- 3) 为 author_id 和 visibility 添加联合索引，以便快速查询特定作者和可见性（如公开、草稿等）的帖子
        CREATE INDEX idx_posts_author_visibility ON posts (author_id, visibility);
    """

    __tablename__ = "posts"

    # 系统主键：自增
    _id = Column(Integer, primary_key=True, autoincrement=True)  # 系统主键ID，系统用，不对外暴露
    # 业务主键：UUID，唯一且不自增1
    pid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))  # 用户的业务主键（UUID形式）

    author_id = Column(String(36), ForeignKey("users.uid"), nullable=False)          # 帖子作者 ID
    visibility = Column(SmallInteger, default=PostVisibility.PUBLIC.value)           # 可见性（0:公开, 1:仅作者）
    publish_status = Column(SmallInteger, default=PostPublishStatus.PUBLISHED.value) # 发布状态（0:草稿, 1:发布）
    review_status = Column(SmallInteger, default=PostReviewStatus.PENDING.value)     # 审核状态（0:待审, 1:通过, 2:拒绝）
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)  # 审核时间
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)   # 软删除时间戳

    # 反向引用：该帖子的作者
    author = relationship("User", back_populates="posts")
    # 双向引用：该帖子的评论
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    # 单向引用：该帖子的内容
    post_content = relationship("PostContent", uselist=False, cascade="all, delete-orphan")
    # 单向引用：该帖子的统计信息
    post_stats = relationship("PostStats", uselist=False, cascade="all, delete-orphan") 
    
    # 帖子本身可以展示点赞数，无需额外点赞表关联
    # 单向引用：该帖子的点赞
    # 还是使用 relationship 关联点赞表与帖子表之间的数据，为了方便查询哪些用户点赞这篇帖子
    likes = relationship("Like", primaryjoin="and_(Like.target_id == Post.pid, Like.target_type == 0)", foreign_keys="Like.target_id", viewonly=True, cascade="all, delete-orphan")

    __table_args__ = (
        # 保证业务主键 pid 唯一
        UniqueConstraint('pid', name='unique_pid'),
        # 索引与上面的 SQL 一致（让 ORM 自动建索引）
        Index("idx_posts_author_id", "author_id"),
        Index("idx_posts_visibility_review_status", "visibility", "review_status"),
        Index("idx_posts_author_visibility", "author_id", "visibility"),
    )