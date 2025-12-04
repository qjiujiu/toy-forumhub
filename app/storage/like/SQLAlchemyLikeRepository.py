# app/storage/like/SQLAlchemyLikeRepository.py

from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from app.models.like import Like, LikeTargetType
from app.schemas.like import (
    LikeCreate,
    LikeCancel,
    LikeOut,
    LikeAdminOut,
    BatchLikesOut,
    BatchLikesAdminOut,
)
from app.storage.like.like_interface import ILikeRepository
from app.core.db import transaction
from app.core.time import now_utc8  # 和你其它模型保持一致的东八区时间
from app.core.exceptions import AlreadyLikedError, NotLikedError

class SQLAlchemyLikeRepository(ILikeRepository):
    """
    使用 SQLAlchemy 实现的点赞仓库
    业务层依赖 ILikeRepository 接口，而不是这个具体实现
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- 内部基础查询 ----------

    def _active_query(self):
        """只查未软删除的点赞"""
        return (
            self.db.query(Like)
            .filter(Like.deleted_at.is_(None))
            # .options(
            #     joinedload(Like.user),    # 方便直接返回 user / post / comment
            #     joinedload(Like.post),
            #     joinedload(Like.comment),
            # )
        )

    def _admin_query(self):
        """管理员查询：不过滤 deleted_at"""
        return (
            self.db.query(Like)
            # .options(
            #     joinedload(Like.user),
            #     joinedload(Like.post),
            #     joinedload(Like.comment),
            # )
        )

    # ---------- 创建 / 恢复点赞 ----------

    def like(self, data: LikeCreate) -> LikeOut:
        """
        创建或恢复点赞：
        - 如存在软删除记录 => 恢复点赞（deleted_at=NULL, created_at=now）
        - 如存在有效记录 => 抛 AlreadyLikedError（阻止重复点赞导致的计数增加）
        """
        existing: Optional[Like] = (
            self._admin_query()
            .filter(
                Like.user_id == data.user_id,
                Like.target_type == int(data.target_type),
                Like.target_id == data.target_id,
            )
            .first()
        )

        now = now_utc8()

        # -------- 情况 1：已有记录 --------
        if existing:
            if existing.deleted_at is not None:
                # 软删除状态 → 恢复点赞（这算一次“新增点赞”，需要 +1）
                with transaction(self.db):
                    existing.deleted_at = None
                    existing.created_at = now

                self.db.refresh(existing)
                return LikeOut.model_validate(existing)

            # 已经是有效点赞 → 抛业务异常，通知上层不要重复 +1
            raise AlreadyLikedError(
                user_id=data.user_id,
                target_type=data.target_type,
                target_id=data.target_id,
            )

        # -------- 情况 2：全新点赞 --------
        like = Like(
            user_id=data.user_id,
            target_type=int(data.target_type),
            target_id=data.target_id,
            created_at=now,
            deleted_at=None,
        )

        with transaction(self.db):
            self.db.add(like)

        self.db.refresh(like)
        return LikeOut.model_validate(like)

    # ---------- 取消点赞（软删） ----------

    def cancel_like(self, data: LikeCancel) -> LikeOut:
        """
        取消点赞（软删除）：
        - 使用 _admin_query 查出记录（包括软删）
        - 如果没有记录：说明从未点过赞 -> 抛 NotLikedError
        - 如果 deleted_at 不为 None：说明已经取消过赞 -> 抛 NotLikedError
        - 否则：当前为已点赞状态 -> 设置 deleted_at，表示本次取消生效
        """
        like: Optional[Like] = (
            self._admin_query()
            .filter(
                Like.user_id == data.user_id,
                Like.target_type == int(data.target_type),
                Like.target_id == data.target_id,
            )
            .first()
        )

        # 1) 完全没这条记录：从来没点赞过
        if like is None:
            raise NotLikedError(
                user_id=data.user_id,
                target_type=data.target_type,
                target_id=data.target_id,
                message=(
                f"user {data.user_id} has not liked "
                f"target_type={data.target_type}, target_id={data.target_id}"
                )
            )

        # 2) 有记录但已经是软删除：说明之前已经取消过点赞
        if like.deleted_at is not None:
            raise NotLikedError(
                user_id=data.user_id,
                target_type=data.target_type,
                target_id=data.target_id,
                message=(
                    f"user {data.user_id} already unliked "
                    f"target_type={data.target_type}, target_id={data.target_id}"
                    )
            )

        # 3) 有记录且 deleted_at is None：当前是“已点赞”状态，本次取消有效
        with transaction(self.db):
            like.deleted_at = now_utc8()

        self.db.refresh(like)
        return LikeOut.model_validate(like)

    # ---------- 查询：普通视角（过滤软删） ----------

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
        - 按 created_at 倒序
        """
        base_q = (
            self._active_query()
            .filter(
                Like.target_type == int(target_type),
                Like.target_id == target_id,
            )
            .order_by(Like.created_at.desc())
        )

        total = base_q.count()

        likes: List[Like] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items = [LikeOut.model_validate(l) for l in likes]

        return BatchLikesOut(
            total=total,
            count=len(items),
            items=items,
        )

    def list_likes_by_user(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> BatchLikesOut:
        """
        查询某个用户的有效点赞记录（分页）：
        - 包含针对帖子和评论的所有点赞
        - 按 created_at 倒序
        """
        base_q = (
            self._active_query()
            .filter(Like.user_id == user_id)
            .order_by(Like.created_at.desc())
        )

        total = base_q.count()

        likes: List[Like] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items = [LikeOut.model_validate(l) for l in likes]

        return BatchLikesOut(
            total=total,
            count=len(items),
            items=items,
        )

    # ---------- 查询：管理员视角（含软删） ----------

    def admin_list_likes_by_target(
        self,
        target_type: LikeTargetType,
        target_id: str,
        page: int,
        page_size: int,
    ) -> BatchLikesAdminOut:
        """
        管理员查询：某个目标的所有点赞（包含软删除）
        """
        base_q = (
            self._admin_query()
            .filter(
                Like.target_type == int(target_type),
                Like.target_id == target_id,
            )
            .order_by(Like.created_at.desc())
        )

        total = base_q.count()

        likes: List[Like] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items = [LikeAdminOut.model_validate(l) for l in likes]

        return BatchLikesAdminOut(
            total=total,
            count=len(items),
            items=items,
        )

    def admin_list_likes_by_user(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> BatchLikesAdminOut:
        """
        管理员查询：某个用户的所有点赞（包含软删）
        """
        base_q = (
            self._admin_query()
            .filter(Like.user_id == user_id)
            .order_by(Like.created_at.desc())
        )

        total = base_q.count()

        likes: List[Like] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items = [LikeAdminOut.model_validate(l) for l in likes]

        return BatchLikesAdminOut(
            total=total,
            count=len(items),
            items=items,
        )
