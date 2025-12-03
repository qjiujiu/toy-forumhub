from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint, Index, SmallInteger
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base
from enum import IntEnum
from app.core.time import now_utc8

# 评论的审核制度采用 先发后审：用户评论直接展示，后台异步审核，检测到违规在前端折叠或删除
# 后续可以采用人工加机器结合的方式审

# 评论显示状态
class CommentStatus(IntEnum):
    NORMAL = 0    # 正常展示
    FOLDED = 1    # 折叠（低质量/被投票降低等）

# 审核状态
class ReviewStatus(IntEnum):
    PENDING  = 0  # 待审
    APPROVED = 1  # 通过
    REJECTED = 2  # 拒绝

class Comment(Base):
    """ 评论区表，存储帖子相关的评论区信息，包括父评论、评论区的总数等。

        CREATE TABLE IF NOT EXISTS comments (
            _id INT AUTO_INCREMENT PRIMARY KEY,               -- 系统主键（自增）
            cid VARCHAR(36) NOT NULL UNIQUE,                  -- 业务主键（UUID，对外使用）
            post_id VARCHAR(36) NOT NULL,                     -- 评论ID（FK -> posts.pid）
            comment_count INT DEFAULT 0,                      -- 评论的评论数
            author_id VARCHAR(36) NOT NULL,                   -- 评论作者业务主键（FK -> users.uid）
            parent_id VARCHAR(36) NULL,                       -- 父评论业务主键
            root_id VARCHAR(36) NULL,                         -- 顶级评论业务主键（整楼聚合）
            like_count INT NOT NULL DEFAULT 0,                -- 评论点赞数（物化计数）
            status TINYINT NOT NULL DEFAULT 0,                -- 0 正常 / 1 折叠
            review_status TINYINT NOT NULL DEFAULT 0,         -- 0 待审 / 1 通过 / 2 拒绝
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,                              -- 创建时间
            reviewed_at TIMESTAMP NULL,                                                           -- 审核时间
            deleted_at TIMESTAMP NULL,                                                            -- 软删除

            FOREIGN KEY (post_id) REFERENCES posts(pid),      -- 外键关联到用户表
            FOREIGN KEY (author_id) REFERENCES users(uid)     -- 外键关联到用户表
        );
    """
    
    __tablename__ = "comments"

    # 系统主键（自增）
    _id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    cid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    # 评论ID
    post_id = Column(String(36), ForeignKey("posts.pid"), nullable=False)
    # 评论数
    comment_count = Column(Integer, default=0)
    # 评论作者 ID
    author_id = Column(String(36), ForeignKey("users.uid"), nullable=False)
    # 父评论 ID（可为空）
    parent_id = Column(String(36), nullable=True)
    # 顶级评论 ID
    root_id = Column(String(36), nullable=True)
    # 点赞数
    like_count = Column(Integer, default=0, nullable=False)
    # 评论状态（正常/折叠）
    status = Column(SmallInteger, default=CommentStatus.NORMAL.value, nullable=False)
    # 审核状态（待审/通过/拒绝）
    review_status = Column(SmallInteger, default=ReviewStatus.PENDING.value, nullable=False)
    # 审核时间
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=now_utc8)  # 创建时间
    # 软删除时间戳
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # 反向引用：该评论区的作者
    author = relationship("User", back_populates="comments")
    # 反向引用：该帖子的评论总览信息（包含帖子ID），可能希望通过评论跳转帖子
    post = relationship("Post", back_populates="comments")
    # 单向引用：该评论区的评论内容
    comment_content = relationship("CommentContent", uselist=False, cascade="all, delete-orphan")
    # 单向引用：该评论区的点赞
    likes = relationship("Like", primaryjoin="and_(Like.target_id == Comment.cid, Like.target_type == 1)", foreign_keys="Like.target_id", viewonly=True,)

    __table_args__ = (
        UniqueConstraint('cid', name='unique_cid'),
        Index("idx_comments_author", "author_id"),
        Index("idx_comments_parent", "parent_id"),
        Index("idx_comments_root", "root_id"),
    )