from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
import datetime
import uuid
from app.models.base import Base
from sqlalchemy import Enum as SAEnum  # SQLAlchemy 数据类型
from enum import Enum as PyEnum  # Python 原生枚举


class PostContent(Base):
    """ 帖子内容表，存储帖子的标题和内容。

        CREATE TABLE IF NOT EXISTS post_contents (
            id INT AUTO_INCREMENT PRIMARY KEY,           -- 系统主键（自增）
            pcid VARCHAR(36) UNIQUE,                     -- 业务主键PID（UUID）
            title VARCHAR(255) NOT NULL,                  -- 帖子标题
            content TEXT NOT NULL                        -- 帖子内容
        );
    """
    
    __tablename__ = "post_contents"

    # 系统主键（自增）
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    pcid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)  # 帖子标题
    content = Column(Text, nullable=False)  # 帖子内容