from typing import Optional, Protocol
from datetime import datetime

from app.schemas.v2.user import (
    UserCreate,
    UserOut,
    BatchUsersOut,
)


class IUserRepository(Protocol):
    """
    用户仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源（MySQL/PG/Mongo 等）
    """

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        """
        根据 uid 或 phone 查询用户
        通过传参控制通过不同字段查找
        """
        ...

    def list_users(
        self,
        username: Optional[str] = None,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        """
        根据用户名查询或分页获取用户列表
        username 为 None 时获取所有用户
        """
        ...

    def create_user(self, user_data: UserCreate) -> UserOut:
        """
        创建用户
        """
        ...

    def update_user(self, uid: str, **kwargs) -> Optional[UserOut]:
        """
        通用更新用户
        通过 kwargs 传入要更新的字段，支持：user_info, status, role, deleted_at, password 等
        软删除通过 deleted_at=True 传入
        """
        ...

    def delete_user(self, uid: str) -> bool:
        """
        硬删除用户
        """
        ...

    def get_password(self, uid: str) -> Optional[str]:
        """
        获取用户密码（用于验证）
        """
        ...