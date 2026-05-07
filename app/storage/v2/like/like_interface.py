from typing import Optional, Protocol

from app.schemas.v2.like import (
    LikeCreate,
    LikeCancel,
    LikeDto,
    LikeOut,
    BatchLikesOut,
)


class ILikeRepository(Protocol):
    """点赞数据层抽象协议。

    likes 表无「更新」语义，只有 创建/恢复、查询、取消（软删除）三种操作。
    """

    def create_or_restore(self, data: LikeCreate) -> LikeOut:
        """
        创建点赞或恢复已取消的点赞。

        查找 (user_id, target_type, target_id) 记录：
        - 不存在 → 创建新记录，created_at=now, updated_at=now
        - 存在且 deleted_at IS NULL → 抛 AlreadyLikedError（幂等拒绝）
        - 存在且 deleted_at IS NOT NULL → 重置 deleted_at=NULL, updated_at=now
        返回 LikeOut。
        """
        ...

    def get_likes(
        self,
        query: LikeDto,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchLikesOut:
        """
        按字段动态过滤查询点赞列表（分页）。

        根据 query 中非 None 字段组合 WHERE 条件：
        - user_id + target_type = 查某用户在某类型下的全部点赞
        - target_type + target_id = 查某内容的点赞用户列表
        - 三个字段全传 = 查特定记录是否存在
        - 自动过滤已软删除（deleted_at IS NULL）
        - 按 _id 倒序
        """
        ...

    def cancel(self, data: LikeCancel) -> bool:
        """
        取消点赞（软删除）。

        查找 (user_id, target_type, target_id) 记录：
        - 不存在 → 抛 NotLikedError
        - 存在且 deleted_at IS NOT NULL → 抛 NotLikedError（已取消过）
        - 存在且 deleted_at IS NULL → 设 deleted_at=now
        返回 True。
        """
        ...
