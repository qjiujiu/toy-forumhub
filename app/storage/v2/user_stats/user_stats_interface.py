from typing import Optional, Protocol

from app.schemas.v2.user_stats import (
    UserStatsDto,
    UserStatsWithUserOut,
)


class IUserStatsRepository(Protocol):
    """
    用户关注/粉丝统计表仓库接口（数据层抽象接口）
    """

    def find_stats(self, user_id: str, with_user: bool = False) -> Optional[UserStatsWithUserOut]:
        """
        根据 user_id 查询统计信息
        with_user=True 时返回带用户信息的统计（用于详情页）
        """
        ...

    def get_or_create_stats(self, user_id: str) -> UserStatsDto:
        """
        获取用户统计，如果不存在则创建
        """
        ...

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> Optional[UserStatsDto]:
        """
        批量更新统计
        following_step: 关注数增量（可为负）
        followers_step: 粉丝数增量（可为负）
        """
        ...

    def delete_stats(self, user_id: str) -> bool:
        """
        删除用户统计
        """
        ...