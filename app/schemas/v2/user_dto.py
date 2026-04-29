from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator
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


class UserOut(BaseModel):
    """用户对外/跨层传输 DTO（不包含敏感字段的聚合结构）"""

    uid: str
    user_info: UserInfoDto
    user_data: UserTimeDto

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _accept_flat_dict(cls, data):
        """允许从扁平 dict 构造嵌套结构。

        mock 数据/脚本导入往往是扁平行数据（username/phone/role/... 与 created_at/... 同级）。
        这里把它转换为 UserOut 所需的 user_info/user_data 嵌套结构。
        """

        if not isinstance(data, dict):
            return data

        # 如果已经包含, 直接嵌套结构了, 直接返回
        if "user_info" in data or "user_data" in data:
            return data

        info_keys = {"username", "phone", "email", "avatar_url", "bio", "role", "status"}
        time_keys = {"last_login_at", "created_at", "updated_at", "deleted_at"}

        info = {k: data.get(k) for k in info_keys if k in data}
        time = {k: data.get(k) for k in time_keys if k in data}

        # 避免顶层遗留扁平字段造成“重复语义”；UserOut 默认 extra=ignore，保持干净更好。
        nested_data = dict(data)
        for k in info_keys.union(time_keys):
            nested_data.pop(k, None)

        nested_data["user_info"] = info
        nested_data["user_data"] = time
        return nested_data


class BatchUsersOut(BaseModel):
    """用户列表/分页 DTO"""

    total: int
    count: int
    users: List[UserOut]

    model_config = ConfigDict(from_attributes=True)
