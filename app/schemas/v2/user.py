"""聚合导出（兼容旧导入路径：app.schemas.v2.user）

语义拆分后的文件：
- user_dto.py: 跨层 DTO
- user_req.py: 请求体
- user_resp.py: 响应体
"""

from app.models.v2.user import UserRole, UserStatus
from app.schemas.v2.user_dto import UserInfoDto, UserTimeDto, UserUpdateDto, UserOut, BatchUsersOut
from app.schemas.v2.user_req import (
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    AdminOperation,
    UserInfoUpdateDto,
)


__all__ = [
    "UserRole",
    "UserStatus",
    "UserInfoDto",
    "UserTimeDto",
    "UserUpdateDto",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "AdminOperation",
    "UserInfoUpdateDto",
    "UserOut",
    "BatchUsersOut",
]
