from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.v2.user import UserRole, UserStatus


class UserInfoDto(BaseModel):
    username: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserTimeDto(BaseModel):
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserUpdateDto(BaseModel):
    password: Optional[str] = None
    user_info: Optional[UserInfoDto] = None
    user_data: Optional[UserTimeDto] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserOut(BaseModel):
    """用户对外/跨层传输 DTO（不包含敏感字段的聚合结构）"""

    uid: str
    user_info: UserInfoDto
    user_data: UserTimeDto

    model_config = ConfigDict(from_attributes=True)


class BatchUsersOut(BaseModel):
    """用户列表/分页 DTO"""

    total: int
    count: int
    users: List[UserOut]

    model_config = ConfigDict(from_attributes=True)
