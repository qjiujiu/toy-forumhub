from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base
from sqlalchemy import Enum as SAEnum  # SQLAlchemy 数据类型
from enum import Enum as PyEnum  # Python 原生枚举

# 评论显示状态
class CommentStatus(PyEnum):
    NORMAL = 0    # 正常展示
    FOLDED = 1    # 折叠（低质量/被投票降低等）

# 审核状态
class ReviewStatus(PyEnum):
    PENDING  = 0  # 待审
    APPROVED = 1  # 通过
    REJECTED = 2  # 拒绝

class CommentSection(Base):
    """ 评论区表，存储帖子相关的评论区信息，包括父评论、评论区的总数等。

        CREATE TABLE IF NOT EXISTS comment_sections (
            id INT AUTO_INCREMENT PRIMARY KEY,             -- 系统主键（自增）
            csid VARCHAR(36) NOT NULL UNIQUE,              -- 业务主键（UUID，对外使用）
            count INT DEFAULT 0,                           -- 评论的评论数
            author_id VARCHAR(36) NOT NULL,                -- 评论作者业务主键（FK -> users.uid）
            parent_id VARCHAR(36) NULL,                    -- 父评论业务主键（FK -> comments.cid）
            root_id VARCHAR(36) NOT NULL,                  -- 顶级评论业务主键（整楼聚合）
            like_count INT NOT NULL DEFAULT 0,             -- 评论点赞数（物化计数）
            status TINYINT NOT NULL DEFAULT 0,             -- 0 正常 / 1 折叠
            review_status TINYINT NOT NULL DEFAULT 0,      -- 0 待审 / 1 通过 / 2 拒绝
            reviewed_at TIMESTAMP NULL,                    -- 审核时间
            deleted_at TIMESTAMP NULL,                     -- 软删除
            commentcontent_id VARCHAR(36) NOT NULL,        -- 评论内容的业务id，关联评论内容表中的 ccid
            FOREIGN KEY (author_id) REFERENCES users(uid),  -- 外键关联到用户表
            FOREIGN KEY (parent_id) REFERENCES comments(cid), -- 外键关联父评论表
            FOREIGN KEY (commentcontent_id) REFERENCES comment_contents(ccid)  -- 外键关联评论内容表
        );
    """
    
    __tablename__ = "comment_sections"

    # 系统主键（自增）
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    csid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    # 评论数
    count = Column(Integer, default=0)
    # 评论作者 ID
    author_id = Column(String(36), ForeignKey("users.uid"), nullable=False)
    # 父评论 ID（可为空）
    parent_id = Column(String(36), ForeignKey("comments.cid"), nullable=True)
    # 顶级评论 ID
    root_id = Column(String(36), nullable=False)
    # 点赞数
    like_count = Column(Integer, default=0, nullable=False)
    # 评论状态（正常/折叠）
    status = Column(SAEnum(CommentStatus), default=CommentStatus.NORMAL, nullable=False)
    # 审核状态（待审/通过/拒绝）
    review_status = Column(SAEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    # 审核时间
    reviewed_at = Column(TIMESTAMP, nullable=True)
    # 软删除时间戳
    deleted_at = Column(TIMESTAMP, nullable=True)
    # 评论内容的业务主键
    commentcontent_id = Column(String(36), ForeignKey("comment_contents.ccid"), nullable=False)

    # 反向引用：该评论区的作者
    author = relationship("User", back_populates="comment_sections")
    # 反向引用：该帖子的评论总览信息（包含帖子ID），可能希望通过评论跳转帖子
    comment = relationship("Comment", back_populates="comment_sections")
    # 单向引用：该评论区的评论内容
    comment_content = relationship("CommentContent")
    # 单向引用：该评论区的点赞
    likes = relationship("Like")

    __table_args__ = (
        UniqueConstraint('csid', name='unique_csid'),
        Index("idx_comment_sections_author", "author_id"),
        Index("idx_comment_sections_parent", "parent_id"),
        Index("idx_comment_sections_root", "root_id"),
    )