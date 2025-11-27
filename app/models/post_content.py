from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
import uuid
from app.models.base import Base
from app.core.time import now_utc8

class PostContent(Base):
    """ 帖子内容表，存储帖子的标题和内容。

        CREATE TABLE IF NOT EXISTS post_contents (
            _id INT AUTO_INCREMENT PRIMARY KEY,           -- 系统主键（自增）
            pcid VARCHAR(36) UNIQUE,                      -- 业务主键PID（UUID）
            post_id VARCHAR(36) NOT NULL UNIQUE,          -- 帖子 ID (FK -> posts.pid)
            title VARCHAR(255) NOT NULL,                  -- 帖子标题
            content TEXT NOT NULL,                        -- 帖子内容
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- 更新时间
            FOREIGN KEY (post_id) REFERENCES posts(pid)        -- 外键关联到帖子表
        );
    """
    
    __tablename__ = "post_contents"

    _id = Column(Integer, primary_key=True, autoincrement=True)                                # 系统主键（自增） 
    pcid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))  # 业务主键（UUID，对外使用）
    post_id =  Column(String(36), ForeignKey("posts.pid"), nullable=False)                     # 帖子ID
    title = Column(String(255), nullable=False)                                                # 帖子标题
    content = Column(Text, nullable=False)                                                     # 帖子内容
    created_at = Column(TIMESTAMP(timezone=True), default=now_utc8)                     # 创建时间
    updated_at = Column(TIMESTAMP(timezone=True), default=now_utc8, onupdate=now_utc8)  # 更新时间