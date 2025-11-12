from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base
import uuid
from enum import Enum as PyEnum          # Python 原生枚举
from sqlalchemy import Enum as SAEnum    # SQLAlchemy 数据类型

# 评论的审核制度采用 先发后审：用户评论直接展示，后台异步审核，检测到违规在前端折叠或删除
# 后续可以采用人工加机器结合的方式审

# 评论显示状态
class CommentStatus(PyEnum):
    NORMAL = 0    # 正常展示
    FOLDED = 1    # 折叠（低质量/被投票降低等）

# 审核状态
class ReviewStatus(PyEnum):
    PENDING  = 0  # 待审
    APPROVED = 1  # 通过
    REJECTED = 2  # 拒绝

class Comment(Base):
    """ 评论模型，对应数据库中的 comments 表。
    
        CREATE TABLE IF NOT EXISTS comments (
            id INT AUTO_INCREMENT PRIMARY KEY,                 -- 系统主键（自增，不对外）
            cid VARCHAR(36) NOT NULL UNIQUE,                   -- 业务主键（UUID，对外使用）
            post_id VARCHAR(36) NOT NULL,                      -- 帖子业务主键（FK -> posts.pid）
            author_id VARCHAR(36) NOT NULL,                    -- 作者业务主键（FK -> users.uid）
            parent_id VARCHAR(36) NULL,                        -- 父评论业务主键（FK -> comments.cid）
            root_id VARCHAR(36) NOT NULL,                      -- 顶级评论业务主键（整楼聚合）
            content TEXT NOT NULL,                             -- 评论内容
            like_count INT NOT NULL DEFAULT 0,                 -- 点赞数（物化计数）
            status TINYINT NOT NULL DEFAULT 0,                 -- 0 正常 / 1 折叠
            review_status TINYINT NOT NULL DEFAULT 0,          -- 0 待审 / 1 通过 / 2 拒绝
            reviewed_at TIMESTAMP NULL,                        -- 审核时间
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL,                         -- 软删除

            CONSTRAINT uq_comments_cid UNIQUE (cid),

            CONSTRAINT fk_comments_post
              FOREIGN KEY (post_id)  REFERENCES posts(pid),
            CONSTRAINT fk_comments_author
              FOREIGN KEY (author_id) REFERENCES users(uid),
            CONSTRAINT fk_comments_parent
              FOREIGN KEY (parent_id) REFERENCES comments(cid)
        );

        -- 索引（评论列表/楼中楼/作者页/审核页 常用查询）：
        -- 1) 帖子下按时间翻页（顶级 + 子评都用得到）
        CREATE INDEX idx_comments_post_created    ON comments (post_id, created_at);
        -- 2) 拉整楼（通过 root_id 一次取出整楼，再按时间排序）
        CREATE INDEX idx_comments_post_root       ON comments (post_id, root_id, created_at);
        -- 3) 拉某条评论的直接子回复（楼中楼点击“展开更多回复”）
        CREATE INDEX idx_comments_post_parent     ON comments (post_id, parent_id, created_at);
        -- 4) 用户个人页的评论记录
        CREATE INDEX idx_comments_author_created  ON comments (author_id, created_at);
        -- 5) 审核列表（后台经常按审核状态/时间筛）
        CREATE INDEX idx_comments_review_created  ON comments (review_status, created_at);
    """
    
    __tablename__ = "comments"

    # 系统主键（自增，不对外）
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    cid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("posts.pid"), nullable=False)      # 帖子 ID
    author_id = Column(String(36), ForeignKey("users.uid"), nullable=False)    # 评论作者 ID
    parent_id = Column(String(36), ForeignKey("comments.cid"), nullable=True)  # 父评论 ID（楼中楼）
    root_id = Column(String(36), nullable=False)                               # 顶级评论 ID
    content = Column(Text, nullable=False)                                     # 评论内容
    like_count = Column(Integer, default=0, nullable=False)                    # 点赞数
    status        = Column(SAEnum(CommentStatus), default=CommentStatus.NORMAL,  nullable=False) # 评论状态（0:正常, 1:折叠）
    review_status = Column(SAEnum(ReviewStatus),  default=ReviewStatus.PENDING, nullable=False) # 审核状态（0:待审, 1:通过, 2:拒绝）
    reviewed_at = Column(TIMESTAMP, nullable=True)                                                                       # 审核时间
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)                                     # 创建时间
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)  # 更新时间
    deleted_at = Column(TIMESTAMP, nullable=True)                                                                        # 软删除时间戳

    # 反向引用：该评论的帖子
    post = relationship("Post", back_populates="comments")
    # 反向引用：该评论的作者
    author = relationship("User", back_populates="comments")
    # 反向引用：该评论的父评论（楼中楼）
    parent = relationship("Comment", back_populates="child", remote_side=[cid])
    # 反向引用：该评论的子评论（楼中楼）
    child = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("cid", name="uq_comments_cid"),
        # 索引与上面的 SQL 一致（让 ORM 自动建索引）
        Index("idx_comments_post_created",   "post_id", "created_at"),
        Index("idx_comments_post_root",      "post_id", "root_id", "created_at"),
        Index("idx_comments_post_parent",    "post_id", "parent_id", "created_at"),
        Index("idx_comments_author_created", "author_id", "created_at"),
        Index("idx_comments_review_created", "review_status", "created_at"),
        # 如果用 MySQL 生成列 is_active，可在迁移脚本中补充新增
    )