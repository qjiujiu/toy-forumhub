from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserInfoUpdateDto(BaseModel):
    """普通用户可更新字段（入参专用）"""

    username: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserCreate(BaseModel):
    """创建用户（账号密码注册）"""

    username: str
    password: str
    phone: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserUpdate(BaseModel):
    """普通用户的可更新字段"""

    user_info: UserInfoUpdateDto

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserPasswordUpdate(BaseModel):
    """修改密码（单独接口，避免与普通更新混用）"""

    new_password: str
    old_password: Optional[str] = None  # 第三方绑定后首次设置密码可不传旧密码

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AdminOperation(BaseModel):
    """管理员操作请求体，管理员uid用于鉴权，用户uid用于操作"""

    admin_uid: str
    user_uid: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")

