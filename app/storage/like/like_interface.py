# app/storage/like/like_interface.py

from typing import Optional, List, Protocol

from app.models.like import LikeTargetType
from app.schemas.like import (
    LikeCreate,
    LikeCancel,
    LikeOut,
    LikeAdminOut,
    BatchLikesOut,
    BatchLikesAdminOut,
)


class ILikeRepository(Protocol):
    """
    点赞仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源
    """

    # ---------- 创建 / 取消 ----------

    def like(self, data: LikeCreate) -> LikeOut:
        """
        创建或恢复点赞：
        - 如果不存在记录 => 新建一条点赞记录（deleted_at = NULL）
        - 如果存在且 deleted_at 不为 NULL => 恢复点赞（deleted_at 置 NULL）
        - 如果存在且 deleted_at 为 NULL => 返回当前点赞（幂等）
        """
        ...

    def cancel_like(self, data: LikeCancel) -> bool:
        """
        取消点赞（软删除）：
        - 根据 user_id + target_type + target_id 定位点赞记录
        - 将 deleted_at 设置为当前时间
        - 如果记录不存在或已经是取消状态，返回 False / True 视实现而定（这里实现为：
          找不到记录 -> False；已是取消状态 -> True）
        """
        ...

    # ---------- 查询：普通视角（过滤软删除） ----------

    def list_likes_by_target(
        self,
        target_type: LikeTargetType,
        target_id: str,
        page: int,
        page_size: int,
    ) -> BatchLikesOut:
        """
        查询某个目标（帖子/评论）的所有有效点赞记录（分页）：
        - 过滤 deleted_at IS NULL
        """
        ...

    def list_likes_by_user(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> BatchLikesOut:
        """
        查询某个用户的点赞记录（分页）：
        - 过滤 deleted_at IS NULL
        - 不区分帖子/评论，按时间倒序
        """
        ...

    # ---------- 查询：管理员视角（含软删） ----------

    def admin_list_likes_by_target(
        self,
        target_type: LikeTargetType,
        target_id: str,
        page: int,
        page_size: int,
    ) -> BatchLikesAdminOut:
        """
        管理员查询某个目标的所有点赞（含软删除）
        """
        ...

    def admin_list_likes_by_user(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> BatchLikesAdminOut:
        """
        管理员查询某个用户的所有点赞（含软删除）
        """
        ...
