from typing import Optional, Union
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.v2.user import UserRole, UserStatus


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


# ===================== 内部 Patch / Command（service -> repo） =====================
#
# 说明：这些 Patch 不是对外 API 的请求体（req）或响应体（resp）。
# 它们用于 service 与 repo 之间表达“这次更新打算修改哪些字段”。
#
# 教学点：为什么要把 Patch 类型拆清楚？
# - 如果 repo 暴露一个“万能 update_user(uid, patch)”方法，那么 patch 的类型边界就是“最后一道防线”。
# - 通过不同 patch 类型把字段分组，可以避免普通更新误改 role/status/password/deleted_at 等敏感字段。


class UserInfoPatch(UserInfoUpdateDto):
    """普通用户信息更新 patch (字段范围与 UserInfoUpdateDto 一致) """


class UserPasswordPatch(BaseModel):
    """ 密码更新 patch (hash 要在 service 完成之后再传入) """

    password: str
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserAdminPatch(BaseModel):
    """管理员更新 patch。

    注意：这里允许软删除（deleted_at），以及角色/状态修改。
    - deleted_at 的值通常应由 service 在运行时生成（now），而不是来自外部请求透传。
    """

    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True, 
        extra="forbid",             # 禁止塞入额外值
        use_enum_values=True        # 使用枚举值的 .value 方法来做 model_dump
    )


# repo 的通用更新入口只接收这三类 patch
UserPatch = Union[UserInfoPatch, UserAdminPatch, UserPasswordPatch]
