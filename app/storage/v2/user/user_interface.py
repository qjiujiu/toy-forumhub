from typing import Optional, Protocol
from datetime import datetime

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
        创建用户 (包括用户的统计信息也会被默认创建)
        """
        ...

    # 计信息（聚合能力）
    # 注意：物理存储方面,  user_stats 仍然是一张独立的数据表, 这里“统计表的访问”并入 UserRepository 主要原因是为了向业务层屏蔽细节
    # - repo 职责是屏蔽底层“分表实现细节”，避免 service/api 依赖多个 repo, 数据层要做的就是把底层为了性能而分表设计的数据表, 在逻辑上聚起来
    # - 对于业务层而言，“用户”是一个整体 (Aggregate), 关注数/粉丝数属于用户的聚合内数据,
    # 这一点 PostRepository 合并 post_contents/post_stats 其实是同一个思路。

    def get_stats(self, user_id: str) -> UserStatsDto:
        """获取用户统计

        - 对业务层来说：用户一旦被创建出来，就应该必然拥有一份统计信息（默认 0/0）。
            Post 聚合的思路也是如初一撤的: 帖子创建出来就应该同时拥有内容、统计信息。

        - 对数据访问层来说：repo 要做的是“聚合写入”来保证不变量，而不是在读路径上悄悄补数据。
          如果某个 user_id 查询不到统计记录，这是属于数据不一致 (例如历史数据缺失/迁移漏跑) 问题, 理论上不应该发生
          更合适的处理是：
          - 直接让调用方感知到异常（例如抛出数据不一致错误）
          - 通过显式的 backfill(兜底) 脚本修复数据
        """
        ...

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> Optional[UserStatsDto]:
        """增量更新关注/粉丝计数（计数不应被更新到负数）。"""
        ...

    def get_user_profile(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        """返回用户详情：UserOut + UserStatsDto（用于个人主页/详情页）。"""
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
