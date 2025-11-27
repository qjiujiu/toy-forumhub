from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid

# 评论的审核制度采用 先发后审：用户评论直接展示，后台异步审核，检测到违规在前端折叠或删除
# 后续可以采用人工加机器结合的方式审

class PostStats(Base):
    """ 帖子统计表，存储帖子的统计数据，比如评论数点赞数，后续可扩展。

        CREATE TABLE IF NOT EXISTS post_stats (
            _id INT AUTO_INCREMENT PRIMARY KEY,                -- 系统主键（自增）
            psid VARCHAR(36) NOT NULL UNIQUE,                  -- 业务主键（UUID，对外使用）
            post_id VARCHAR(36) NOT NULL UNIQUE,               -- 帖子业务主键（FK -> posts.pid）
            like_count INT DEFAULT 0,                          -- 点赞数
            comment_count INT DEFAULT 0,                       -- 帖子总评论数
            FOREIGN KEY (post_id) REFERENCES posts(pid)        -- 外键关联到帖子表
        );
    """

    __tablename__ = "post_stats"

    # 系统主键（自增）
    _id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    psid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    # 帖子 ID
    post_id = Column(String(36), ForeignKey("posts.pid"), nullable=False)
    # 帖子点赞数
    like_count = Column(Integer, default=0)  
    # 帖子总评论数
    comment_count = Column(Integer, default=0)
    # 后续可扩展收藏数，转发数
    
    __table_args__ = (
        UniqueConstraint('psid', name='unique_psid'),
        Index("idx_post_stats_post_id", "post_id"),
    )