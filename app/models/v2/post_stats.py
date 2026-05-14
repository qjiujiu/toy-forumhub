from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint, TIMESTAMP
from app.models.v2.base import Base
import uuid
from app.kit.time import now_utc8

class PostStats(Base):
    """ 帖子统计表，存储帖子的统计数据，比如评论数点赞数，后续可扩展。

        CREATE TABLE IF NOT EXISTS post_stats (
            _id INT AUTO_INCREMENT PRIMARY KEY,                -- 系统主键（自增）
            psid VARCHAR(36) NOT NULL UNIQUE,                  -- 业务主键（UUID，对外使用）
            post_id VARCHAR(36) NOT NULL UNIQUE,               -- 帖子业务主键（FK -> posts.pid）
            like_count INT DEFAULT 0,                          -- 点赞数
            comment_count INT DEFAULT 0,                       -- 帖子总评论数
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- 创建时间
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
    # 用于热帖排序的更新时间，点赞数或评论数变化时更新
    created_at = Column(TIMESTAMP(timezone=True), default=now_utc8)
    
    __table_args__ = (
        UniqueConstraint('psid', name='unique_psid'),
        Index("idx_post_stats_post_id", "post_id"),
    )