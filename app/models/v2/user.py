from sqlalchemy import Column, Integer, String, SmallInteger, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import relationship
import datetime
import uuid
from app.models.v2.base import Base
from enum import IntEnum  
from app.core.time import now_utc8

class UserRole(IntEnum):
    NORMAL_USER = 0 # 普通用户
    MODERATOR = 1   # 审核员
    ADMIN = 2       # 管理员

class UserStatus(IntEnum):
    NORMAL = 0  # 正常
    BANNED = 1  # 封禁
    FROZEN = 2  # 冻结

class User(Base):
    """ 用户模型，对应数据库中的 users 表。
    
        CREATE TABLE IF NOT EXISTS users (
            _id INT AUTO_INCREMENT PRIMARY KEY,        -- 系统主键 ID
            uid VARCHAR(36) UNIQUE,                   -- 用户的业务主键（UUID）
            username VARCHAR(100) NOT NULL,           -- 用户昵称
            role SMALLINT DEFAULT 0,                  -- 用户角色（0: 普通用户，1: 审核员，2: 管理员）
            status SMALLINT DEFAULT 0,                -- 用户状态（0: 正常，1: 封禁，2: 冻结）
            phone VARCHAR(50) UNIQUE NOT NULL,        -- 电话
            password VARCHAR(255) NOT NULL,           -- 密码
            avatar_url VARCHAR(255),                  -- 用户头像 URL
            email VARCHAR(100) UNIQUE,                -- 邮箱（可为空）
            bio TEXT,                                 -- 用户简介
    
            last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 最后登录时间
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- 更新时间
            deleted_at TIMESTAMP NULL                 -- 软删除时间戳
        );
    """
    
    __tablename__ = "users"
    _id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), nullable=False)
    avatar_url = Column(String(255), nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SmallInteger, default=UserRole.NORMAL_USER.value)
    bio = Column(Text, nullable=True)
    status = Column(SmallInteger, default=UserStatus.NORMAL.value)
    last_login_at = Column(TIMESTAMP(timezone=True), default=now_utc8)
    created_at = Column(TIMESTAMP(timezone=True), default=now_utc8)
    updated_at = Column(TIMESTAMP(timezone=True), default=now_utc8, onupdate=now_utc8)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    likes = relationship("Like")
    userstats = relationship("UserStats", uselist=False, cascade="all, delete-orphan")
    followings = relationship("Follow", foreign_keys="Follow.user_id", back_populates="user")
    followers = relationship("Follow", foreign_keys="Follow.followed_user_id", back_populates="followed_user")