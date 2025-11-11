from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base


class Like(Base):
    """ 点赞模型，对应数据库中的 likes 表。
    
        CREATE TABLE IF NOT EXISTS likes (
            lid INT AUTO_INCREMENT PRIMARY KEY,          -- 点赞 ID
            user_id INT,                                 -- 用户 ID
            target_type SMALLINT,                        -- 点赞目标类型（0: 帖子, 1: 评论）
            target_id INT,                               -- 点赞目标 ID（帖子 ID 或 评论 ID）
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 点赞时间
            deleted_at TIMESTAMP NULL,                   -- 软删除时间戳
            FOREIGN KEY (user_id) REFERENCES users(uid),    -- 外键关联到用户表
            FOREIGN KEY (target_id) REFERENCES posts(pid)   -- 外键关联到帖子表，或可以引用评论表
        );
    """
    
    __tablename__ = "likes"

    lid = Column(Integer, primary_key=True, autoincrement=True)  # 点赞 ID
    user_id = Column(Integer, ForeignKey("users.uid"), nullable=False)  # 用户 ID
    target_type = Column(SmallInteger, nullable=False)  # 点赞目标类型（0: 帖子, 1: 评论）
    target_id = Column(Integer, nullable=False)  # 点赞目标 ID（帖子或评论 ID）
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)  # 点赞时间
    deleted_at = Column(TIMESTAMP, nullable=True)  # 软删除时间戳

    # 反向引用：该点赞的用户
    user = relationship("User", back_populates="likes")
    # 反向引用：该点赞的帖子（如果是帖子点赞）
    post = relationship("Post", back_populates="likes", uselist=False)
    # 反向引用：该点赞的评论（如果是评论点赞）
    comment = relationship("Comment", back_populates="likes", uselist=False)