from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base
from app.core.time import now_utc8

class Follow(Base):
    """ 用户关注关系表，记录用户关注了哪些用户 
        
        CREATE TABLE IF NOT EXISTS follows (
            _id INT AUTO_INCREMENT PRIMARY KEY,              -- 系统主键（自增）
            user_id VARCHAR(36) NOT NULL,                    -- 关注者ID (FK -> users.uid)
            followed_user_id VARCHAR(36) NOT NULL,           -- 被关注者ID (FK -> users.uid)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            deleted_at TIMESTAMP NULL,                       -- 软删除时间戳（用于取消关注）

            CONSTRAINT fk_follow_user FOREIGN KEY (user_id) REFERENCES users(uid),            -- 外键：关注者
            CONSTRAINT fk_followed_user FOREIGN KEY (followed_user_id) REFERENCES users(uid), -- 外键：被关注者

            CONSTRAINT uq_user_follow UNIQUE (user_id, followed_user_id)    -- 联合唯一约束：防止用户重复关注
        );

        -- 为了快速查询用户的关注者和粉丝，可以添加以下索引：
        CREATE INDEX idx_follow_user ON follows (user_id);
        CREATE INDEX idx_followed_user ON follows (followed_user_id);
    
    """
    
    __tablename__ = "follows"

    # 系统主键（自增）
    _id = Column(Integer, primary_key=True, autoincrement=True)
    # 关注者ID
    user_id = Column(String(36), ForeignKey("users.uid"), nullable=False)
    # 被关注者ID
    followed_user_id = Column(String(36), ForeignKey("users.uid"), nullable=False)
    # 记录创建时间
    created_at = Column(TIMESTAMP(timezone=True), default=now_utc8)
    # 软删除时间戳（用于取消关注）
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # 反向引用：该关注记录的关注者
    user = relationship("User", foreign_keys=[user_id], back_populates="followers")
    # 反向引用：该关注记录的被关注者
    followed_user = relationship("User", foreign_keys=[followed_user_id], back_populates="followers")

    __table_args__ = (
        # 联合唯一约束：确保每个用户只能关注一次某个用户
        UniqueConstraint("user_id", "followed_user_id", name="uq_user_follow"),
        # 索引：加速查询
        Index("idx_follow_user", "user_id"),
        Index("idx_followed_user", "followed_user_id"),
    )