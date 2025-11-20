from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import datetime
import uuid
from app.models.base import Base
from app.core.time import now_utc8
class CommentContent(Base):
    """ 评论内容表，存储评论的实际内容。
    
        CREATE TABLE IF NOT EXISTS comment_contents (
            _id INT AUTO_INCREMENT PRIMARY KEY,             -- 系统主键（自增）
            ccid VARCHAR(36) NOT NULL UNIQUE,               -- 业务主键（UUID，对外使用）
            comment_id VARCHAR(36) NOT NULL,                -- 评论ID（FK -> comments.cid)
            content TEXT NOT NULL,                          -- 评论内容
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,                             -- 创建时间
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  -- 更新时间
            FOREIGN KEY (comment_id) REFERENCES comments(cid)  -- 外键关联评论内容表
        );
    """
    
    __tablename__ = "comment_contents"

    # 系统主键（自增）
    _id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    ccid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    # 评论区 ID
    comment_id = Column(String(36), ForeignKey("comments.cid"), nullable=False)
    content = Column(Text, nullable=False)  # 评论内容
    created_at = Column(TIMESTAMP(timezone=True), default=now_utc8)  # 创建时间
    updated_at = Column(TIMESTAMP(timezone=True), default=now_utc8, onupdate=now_utc8)  # 更新时间