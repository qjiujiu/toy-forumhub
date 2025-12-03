from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base
import uuid
from enum import IntEnum 
from app.core.time import now_utc8
# 点赞目标类型
class LikeTargetType(IntEnum):
    POST = 0  # 帖子
    COMMENT = 1  # 评论

class Like(Base):
    """ 点赞模型，对应数据库中的 likes 表。
    
        CREATE TABLE IF NOT EXISTS likes (
            _id INT AUTO_INCREMENT PRIMARY KEY,              -- 系统主键（自增）
            lid VARCHAR(36) UNIQUE,                          -- 业务主键（UUID）
            user_id VARCHAR(36) NOT NULL,                    -- 用户 ID (FK -> users.id)
            target_type SMALLINT,                            -- 点赞目标类型（0: 帖子, 1: 评论）
            target_id VARCHAR(36) NOT NULL,                  -- 点赞目标 ID（帖子 ID 或 评论 ID）
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 点赞时间
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- 更新时间
            deleted_at TIMESTAMP NULL,                       -- 软删除时间戳
            
            CONSTRAINT uq_likes_user_target UNIQUE (user_id, target_type, target_id),
            CONSTRAINT fk_likes_user FOREIGN KEY (user_id) REFERENCES users(uid),
            FOREIGN KEY (user_id) REFERENCES users(uid)      -- 外键关联到用户表

        );
        -- 索引建议：
        CREATE INDEX idx_likes_user_target_type ON likes (user_id, target_type);
        CREATE INDEX idx_likes_target_type_id   ON likes (target_type, target_id);
        CREATE INDEX idx_likes_created_at       ON likes (created_at);
    """
    
    __tablename__ = "likes"
    # 系统主键（内部使用，不对外暴露）
    _id = Column(Integer, primary_key=True, autoincrement=True)
    # 业务主键（UUID，对外使用）
    lid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.uid"), nullable=False)  # 用户 ID
    target_type = Column(SmallInteger, nullable=False)  # 点赞目标类型（0: 帖子, 1: 评论）
    target_id = Column(String(36), nullable=False)  # 点赞目标 ID（帖子或评论 ID）
    created_at = Column(TIMESTAMP(timezone=True), default=now_utc8)  # 点赞时间
    updated_at = Column(TIMESTAMP(timezone=True), default=now_utc8, onupdate=now_utc8)  # 更新时间
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)  # 软删除时间戳

    # # 反向引用：该点赞的用户
    # user = relationship("User", back_populates="likes")
    # # 反向引用：该点赞的帖子（如果是帖子点赞）
    # post = relationship("Post", back_populates="likes", uselist=False, primaryjoin="and_(foreign(Like.target_id) == Post.pid, Like.target_type == 0)", viewonly=True)
    # # 反向引用：该点赞的评论区（如果是评论区点赞）
    # comment = relationship("Comment", back_populates="likes", uselist=False, primaryjoin="and_(foreign(Like.target_id) == Comment.cid, Like.target_type == 1)", viewonly=True)
    
    __table_args__ = (
        # 每个用户对同一目标只能点赞一次（业务约束）
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_likes_user_target"),

        # 索引：快速查找某个对象的点赞情况
        Index("idx_likes_user_target_type", "user_id", "target_type"),
        Index("idx_likes_target_type_id", "target_type", "target_id"),
        Index("idx_likes_created_at", "created_at"),
    )