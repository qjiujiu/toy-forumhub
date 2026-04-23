from typing import List, Optional
from pydantic import BaseModel, EmailStr, AnyUrl, ConfigDict
from datetime import datetime
from app.models.user import UserRole, UserStatus

class UserDto(BaseModel):
    username: str
    phone: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class UserCreate(BaseModel):
    """
    创建用户（账号密码注册）
    """
    user_info: UserDto
    password: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class UserOut(BaseModel):
    """
    对外返回的用户基础信息
    """
    uid: str                                     # 业务主键（UUID 字符串）
    user_info: UserDto
    role: UserRole = UserRole.NORMAL_USER        # 角色
    status: UserStatus = UserStatus.NORMAL.value # 状态

    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class BatchUsersOut(BaseModel):
    """
    列表/分页返回
    - total: 满足筛选条件的总数
    - count: 当前这页返回的条数
    - users: 当前页的用户列表
    """
    total: int
    count: int
    users: List[UserOut]

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    """
    更新用户
    """
    user_info: UserDto

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserPasswordUpdate(BaseModel):
    """
    修改密码（单独接口，避免与普通更新混用）
    """
    new_password: str
    old_password: Optional[str] = None  # 第三方绑定后首次设置密码可不传旧密码

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class AdminOperation(BaseModel):
    """
    管理员操作请求体，管理员uid用于鉴权，用户uid用于操作
    """

    admin_uid: str
    user_uid: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")
