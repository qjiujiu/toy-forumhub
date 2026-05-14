from typing import Union, Dict

from app.schemas.v2.like import (
    LikeCreate,
    LikeCancel,
    LikeDto,
    GetUserLike,
    GetTargetLike,
    LikeOut,
    BatchLikesOut,
)
from app.schemas.v2.post_stats import PostStatsDto
from app.schemas.v2.comment import CommentUpdate

from app.models.v2.like import LikeTargetType

from app.storage.v2.like.like_interface import ILikeRepository
from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.comment.comment_interface import ICommentRepository

import logging
logger = logging.getLogger(__name__)
from app.kit.exceptions import AlreadyLikedError, NotLikedError


class LikeService:
    """
    点赞业务层。

    - 点赞/取消点赞后自动更新目标（帖子/评论）的 like_count。
    - 帖子 like_count 通过 post_repo.update_stats() 绝对值覆盖。
    - 评论 like_count 通过 comment_repo.update_counters() 增量更新。
    """

    def __init__(
        self,
        like_repo: ILikeRepository,
        post_repo: IPostRepository,
        comment_repo: ICommentRepository,
    ):
        self._like_repo = like_repo
        self._post_repo = post_repo
        self._comment_repo = comment_repo

    # ==================== C ====================

    def like(self, data: LikeCreate) -> LikeOut:
        """
        点赞（帖子或评论）。

        流程：
        1. 验证目标存在
        2. 调用存储层创建点赞（可能抛 AlreadyLikedError）
        3. 更新目标的 like_count +1
        """
        self._ensure_target_exists(data.target_type, data.target_id)

        like_out = self._like_repo.create_or_restore(data)

        self._increment_like_count(data.target_type, data.target_id, delta=1)

        logger.info(
            f"[LIKE] user={data.user_id} liked "
            f"target_type={data.target_type} target_id={data.target_id}"
        )
        return like_out

    # ==================== D ====================

    def cancel_like(self, data: LikeCancel) -> bool:
        """
        取消点赞（帖子或评论）。

        流程：
        1. 调用存储层取消点赞（可能抛 NotLikedError）
        2. 更新目标的 like_count -1
        """
        result = self._like_repo.cancel(data)

        self._increment_like_count(data.target_type, data.target_id, delta=-1)

        logger.info(
            f"[UNLIKE] user={data.user_id} unliked "
            f"target_type={data.target_type} target_id={data.target_id}"
        )
        return result

    # ==================== R ====================

    def get_user_likes(
        self,
        query: GetUserLike,
        page: int = 0,
        page_size: int = 20,
        to_dict: bool = True,
    ) -> Union[Dict, BatchLikesOut]:
        """
        获取某用户在某类型下的点赞列表。
        - 例如：用户 A 点赞过的所有帖子
        """
        like_query = LikeDto(user_id=query.user_id, target_type=query.target_type)
        result = self._like_repo.get_likes(like_query, page, page_size)
        return result.model_dump() if to_dict else result

    def get_target_likes(
        self,
        query: GetTargetLike,
        page: int = 0,
        page_size: int = 20,
        to_dict: bool = True,
    ) -> Union[Dict, BatchLikesOut]:
        """
        获取某目标（帖子/评论）下的所有点赞用户列表。
        - 例如：帖子 P1 被哪些用户点赞过
        """
        like_query = LikeDto(target_type=query.target_type, target_id=query.target_id)
        result = self._like_repo.get_likes(like_query, page, page_size)
        return result.model_dump() if to_dict else result

    # ==================== 内部辅助 ====================

    def _ensure_target_exists(self, target_type: LikeTargetType, target_id: str) -> None:
        """验证点赞目标（帖子或评论）存在。"""
        if target_type == LikeTargetType.POST:
            post = self._post_repo.get_by_pid(target_id)
            if not post:
                raise ValueError(f"post {target_id} not found")
        elif target_type == LikeTargetType.COMMENT:
            comment = self._comment_repo.get_by_cid(target_id)
            if not comment:
                raise ValueError(f"comment {target_id} not found")
        else:
            raise ValueError(f"invalid target_type={target_type}")

    def _increment_like_count(self, target_type: LikeTargetType, target_id: str, delta: int) -> None:
        """更新点赞数（+1 或 -1），增量语义，计数不下溢由各 repo 保证。"""
        if target_type == LikeTargetType.POST:
            self._post_repo.update_stats(target_id, PostStatsDto(like_count=delta))
        elif target_type == LikeTargetType.COMMENT:
            self._comment_repo.update_counters(target_id, CommentUpdate(like_count=delta))
