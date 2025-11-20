from typing import Optional, List
from pydantic import BaseModel, EmailStr, AnyUrl, ConfigDict
from datetime import datetime
from app.models.user import UserRole, UserStatus

class UserCreate(BaseModel):
    """
    创建用户（账号密码注册）
    """
    username: str
    phone: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    password: str

    # 普通注册使用默认角色和状态，一般情况下只有管理员能更新角色、状态；
    role: Optional[UserRole] = 0
    status: Optional[UserStatus] = 0

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class UserOut(BaseModel):
    """
    对外返回的用户基础信息（不包含敏感字段，如 password、phone 可按你需求放/不放）
    """
    uid: str                                     # 业务主键（UUID 字符串）
    username: str                                # 昵称
    avatar_url: Optional[str] = None             # 头像 URL
    role: UserRole = UserRole.NORMAL_USER        # 角色
    bio: Optional[str] = None                    # 简介
    status: UserStatus = UserStatus.NORMAL.value # 状态

    # # 时间戳一般前端也会用到，放在 Out 里更好
    # last_login_at: Optional[datetime] = None
    # created_at: Optional[datetime] = None
    # updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserAllOut(BaseModel):
    """
    对外返回的用户所有信息（包含敏感字段，如 password、phone）
    """
    uid: str                                     # 业务主键（UUID 字符串）
    username: str
    phone: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    password: str

    # 普通注册使用默认角色和状态，一般情况下只有管理员能更新角色、状态；
    role: Optional[UserRole]
    status: Optional[UserStatus]

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class UserDetailOut(UserOut):
    
    # 示例：聚合字段（若你有 UserStatistics 关系）
    # followers: Optional[int] = None
    # following: Optional[int] = None
    # posts_count: Optional[int] = None
    pass


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
    更新用户（部分字段可选）
    - 注意：一般不允许在普通更新接口里直接改角色/状态（除非是管理员接口）
    - 可根据你的权限体系拆成 UserUpdateSelf / AdminUserUpdate
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[AnyUrl] = None
    bio: Optional[str] = None

    # 如果你有“修改密码”接口，建议单独一个 Schema（见下）
    # 这里不直接允许更新 password，避免误用
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AdminUserUpdate(BaseModel):
    """
    管理员更新（可以修改角色、状态等敏感字段）
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[AnyUrl] = None
    bio: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserPasswordUpdate(BaseModel):
    """
    修改密码（单独接口，避免与普通更新混用）
    """
    old_password: Optional[str] = None  # 第三方绑定后首次设置密码可不传旧密码
    new_password: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")
