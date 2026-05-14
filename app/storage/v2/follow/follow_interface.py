from typing import Optional, Protocol

from app.schemas.v2.follow import (
    FollowCreate,
    FollowCancel,
    FollowDto,
    FollowOut,
    BatchFollowsOut,
)


class IFollowRepository(Protocol):
    """关注数据层抽象协议。"""

    def follow(self, data: FollowCreate) -> bool:
        """
        关注用户。

        查找 (user_id, followed_user_id) 记录：
        - 存在且 deleted_at IS NULL → 抛 AlreadyFollowingError
        - 存在且 deleted_at IS NOT NULL → 重置 deleted_at=NULL，返回 True
        - 不存在 → 插入新记录，返回 True
        """
        ...

    def unfollow(self, data: FollowCancel) -> bool:
        """
        取消关注（软删除）。

        查找 (user_id, followed_user_id) 记录：
        - 不存在 → 抛 NotFollowingError
        - 存在且 deleted_at IS NOT NULL → 抛 NotFollowingError（已取消）
        - 存在且 deleted_at IS NULL → 设 deleted_at=now，返回 True
        """
        ...

    def hard_unfollow(self, data: FollowCancel) -> bool:
        """
        硬删除关注记录。

        查找 (user_id, followed_user_id) 记录：
        - 不存在 → 抛 NotFollowingError
        - 存在 → 删除记录，返回 True
        """
        ...

    def get_follows(
        self,
        query: FollowDto,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchFollowsOut:
        """
        按非空字段动态过滤查询关注关系（分页）。

        - user_id → 关注列表（我关注了谁）
        - followed_user_id → 粉丝列表（谁关注了我）
        - 两个字段都传 → 查特定关注关系是否存在
        - 自动过滤已软删除（deleted_at IS NULL）
        """
        ...
