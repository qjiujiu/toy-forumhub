from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import datetime
import uuid
from app.models.base import Base

class CommentContent(Base):
    """ 评论内容表，存储评论的实际内容。
    
        CREATE TABLE IF NOT EXISTS comment_contents (
            id INT AUTO_INCREMENT PRIMARY KEY,             -- 系统主键（自增）
            ccid VARCHAR(36) NOT NULL UNIQUE,               -- 业务主键（UUID，对外使用）
            content TEXT NOT NULL,                          -- 评论内容
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- 更新时间
        );
    """
    
    __tablename__ = "comment_contents"

    # 系统主键（自增）
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    ccid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)  # 评论内容
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)  # 创建时间
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)  # 更新时间