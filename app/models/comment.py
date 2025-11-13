from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

# 评论的审核制度采用 先发后审：用户评论直接展示，后台异步审核，检测到违规在前端折叠或删除
# 后续可以采用人工加机器结合的方式审

class Comment(Base):
    """ 评论表，存储与评论相关的元数据，及其与评论区和帖子内容的关联。

        CREATE TABLE IF NOT EXISTS comments (
            id INT AUTO_INCREMENT PRIMARY KEY,                -- 系统主键（自增）
            cid VARCHAR(36) NOT NULL UNIQUE,                   -- 业务主键（UUID，对外使用）
            post_id VARCHAR(36) NOT NULL,                      -- 帖子业务主键（FK -> posts.pid）
            count INT DEFAULT 0,                               -- 帖子总评论数
            commentsection_id VARCHAR(36) NOT NULL,            -- 评论区id，关联评论区表中的 csid
            FOREIGN KEY (post_id) REFERENCES posts(pid),      -- 外键关联到帖子表
            FOREIGN KEY (commentsection_id) REFERENCES comment_sections(csid)  -- 外键关联到评论区表
        );
    """

    __tablename__ = "comments"

    # 系统主键（自增）
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    cid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    # 帖子 ID
    post_id = Column(String(36), ForeignKey("posts.pid"), nullable=False)
    # 帖子总评论数
    count = Column(Integer, default=0)
    # 评论区 ID，关联评论区表
    commentsection_id = Column(String(36), ForeignKey("comment_sections.csid"), nullable=False)

    # # 反向引用：该评论的帖子
    # post = relationship("Post", back_populates="comments")
    
    # 反向引用：该评论区的评论
    comment_sections = relationship("CommentSection", back_populates="comment")

    __table_args__ = (
        UniqueConstraint('cid', name='unique_cid'),
        Index("idx_comments_post", "post_id"),
        Index("idx_comments_commentsection", "commentsection_id"),
    )