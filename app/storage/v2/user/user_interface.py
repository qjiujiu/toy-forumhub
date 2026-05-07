from typing import Optional, Protocol

from app.schemas.v2.user import (
    UserCreate,
    UserOut,
    BatchUsersOut,
    UserUpdateDto,
)
from app.schemas.v2.user_stats import UserStatsDto, UserStatsWithUserOut


class IUserRepository(Protocol):
    """
    用户仓库接口协议（数据层抽象接口）

    物理上 users / user_stats 仍然是两张独立表，
    但本接口屏蔽多表细节，对外以"一个用户聚合"的形式提供读写能力。
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
        创建用户聚合：一次事务内写入 users + user_stats。
        - 用户一旦创建，必然拥有对应的统计记录（关注数/粉丝数默认 0）。
        - 避免出现"用户存在但统计缺失"的中间态。
        """
        ...

    def update_user(self, uid: str, update_dto: UserUpdateDto) -> Optional[UserOut]:
        """
        更新用户 - 通过 DTO 封装所有可更新字段
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

    # ========== 聚合能力：user_stats ==========

    def get_stats(self, user_id: str) -> UserStatsDto:
        """
        获取用户统计。
        - create_user 已保证统计记录必然存在。
        - 如果查不到统计，视为数据不一致，抛出异常。
        """
        ...

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> UserStatsDto:
        """
        增量更新关注/粉丝计数。
        - 计数不应被更新到负数。
        - create_user 已保证统计记录存在，因此不做隐式创建。
        """
        ...

    def get_user_profile(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        """
        返回用户详情：UserOut + UserStatsDto（用于个人主页/详情页）。
        - 如果用户不存在，返回 None。
        - 如果统计记录缺失（数据不一致），抛异常。
        """
        ...
