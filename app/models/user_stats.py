from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base
from app.core.time import now_utc8

class UserStats(Base):
    """ 用户关注统计表，记录每个用户的关注数和粉丝数 

        CREATE TABLE IF NOT EXISTS user_stats (
            _id INT AUTO_INCREMENT PRIMARY KEY,          -- 系统主键（自增）
            user_id VARCHAR(36) NOT NULL,               -- 用户 ID (FK -> users.uid)
            following_count INT DEFAULT 0,              -- 用户的关注数
            followers_count INT DEFAULT 0,              -- 用户的粉丝数
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
            CONSTRAINT fk_user_stats_user FOREIGN KEY (user_id) REFERENCES users(uid),  -- 外键：关联用户表
            UNIQUE (user_id)   -- 保证每个用户只有一条记录
        );

        -- 索引：加速查询用户的关注数和粉丝数
        CREATE INDEX idx_user_stats_user_id ON user_stats (user_id);
            
    """
    
    __tablename__ = "user_stats"

    # 系统主键（自增）
    _id = Column(Integer, primary_key=True, autoincrement=True)
    # 用户ID（外键，关联用户表）
    user_id = Column(String(36), ForeignKey("users.uid"), nullable=False)
    # 用户关注数
    following_count = Column(Integer, default=0)
    # 用户粉丝数
    followers_count = Column(Integer, default=0)
    # 更新时间
    updated_at = Column(TIMESTAMP(timezone=True), default=now_utc8, onupdate=now_utc8, nullable=False)

    __table_args__ = (
        # 确保每个用户只有一条记录
        UniqueConstraint("user_id", name="unique_user_stats"),
        # 索引：加速查询
        Index("idx_user_stats_user_id", "user_id"),
    )