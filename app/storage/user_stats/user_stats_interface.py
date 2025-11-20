from typing import Optional, Protocol
from datetime import datetime

from app.schemas.user_stats import (
    UserStatsOut,
    UserStatsWithUserOut,
    UserStatsUpdate,
)


class IUserStatsRepository(Protocol):
    """
    用户关注/粉丝统计表仓库接口（数据层抽象接口）
    """

    def get_by_user_id(self, user_id: str) -> Optional[UserStatsOut]:
        """根据 user_id 获取统计信息，若不存在返回 None"""
        ...

    def get_with_user_by_user_id(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        """
        获取携带用户信息的统计信息（用于用户详情页）
        - 内部会 join User 表
        """
        ...

    def create_for_user(self, user_id: str) -> UserStatsOut:
        """
        为指定用户创建统计记录（如果已存在则直接返回现有记录）
        - 默认 following_count = 0, followers_count = 0
        """
        ...

    def update_statistics(self, user_id: str, data: UserStatsUpdate) -> Optional[UserStatsOut]:
        """
        按照 UserStatsUpdate 部分更新统计数据
        - 仅 following_count / followers_count
        - 若记录不存在，返回 None
        """
        ...

    def update_following(self, user_id: str, step: int = 1) -> UserStatsOut:
        """
        增加（或减少）关注数：following_count += step
        - step 可以为负数
        - 若记录不存在，将先创建后更新
        """
        ...

    def update_followers(self, user_id: str, step: int = 1) -> UserStatsOut:
        """
        增加（或减少）粉丝数：followers_count += step
        - step 可以为负数
        - 若记录不存在，将先创建后更新
        """
        ...

    def delete_by_user_id(self, user_id: str) -> bool:
        """
        删除指定用户的统计记录（一般配合用户硬删除使用）
        返回是否删除成功
        """
        ...
