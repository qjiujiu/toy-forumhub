from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.v2.like import Like

from app.schemas.v2.like import (
    LikeCreate,
    LikeCancel,
    LikeDto,
    LikeOut,
    BatchLikesOut,
)

from app.storage.v2.like.like_interface import ILikeRepository

from app.core.time import now_utc8
from app.core.db import transaction
from app.core.exceptions import AlreadyLikedError, NotLikedError


class SQLAlchemyLikeRepository(ILikeRepository):
    """点赞数据层 SQLAlchemy 实现。"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== C ====================

    def create_or_restore(self, data: LikeCreate) -> LikeOut:
        """
        创建新点赞，或恢复已取消的点赞（幂等恢复）。
        """
        existing = (
            self.db.query(Like)
            .filter(Like.user_id == data.user_id)
            .filter(Like.target_type == data.target_type.value)
            .filter(Like.target_id == data.target_id)
            .first()
        )

        now = now_utc8()

        if existing:
            if existing.deleted_at is None:
                # 已经点过赞且未取消 → 幂等拒绝
                raise AlreadyLikedError(data.user_id, data.target_type, data.target_id)

            # 之前取消过 → 恢复：清空 deleted_at，更新 updated_at
            with transaction(self.db):
                existing.deleted_at = None
                existing.updated_at = now
            self.db.refresh(existing)
            return LikeOut.model_validate(existing)

        # 全新点赞
        like = Like(
            user_id=data.user_id,
            target_type=data.target_type.value,
            target_id=data.target_id,
            created_at=now,
            updated_at=now,
        )
        with transaction(self.db):
            self.db.add(like)
        self.db.refresh(like)
        return LikeOut.model_validate(like)

    # ==================== R ====================

    def get_likes(
        self,
        query: LikeDto,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchLikesOut:
        """
        动态字段检索：只过滤 query 中非 None 的字段，自动排除软删除。
        """
        base_q = self.db.query(Like).filter(Like.deleted_at.is_(None))

        for field_name in query.model_fields:
            field_value = getattr(query, field_name, None)
            if field_value is not None:
                model_field = getattr(Like, field_name, None)
                if model_field is not None:
                    # IntEnum → 取其 .value 与 SmallInteger 列比较
                    if hasattr(field_value, 'value'):
                        base_q = base_q.filter(model_field == field_value.value)
                    else:
                        base_q = base_q.filter(model_field == field_value)

        base_q = base_q.order_by(desc(Like._id))

        total = base_q.count()
        likes_orm = base_q.offset(page * page_size).limit(page_size).all()
        items = [LikeOut.model_validate(l) for l in likes_orm]

        return BatchLikesOut(total=total, count=len(items), items=items)

    # ==================== D ====================

    def cancel(self, data: LikeCancel) -> bool:
        """
        取消点赞（软删除）。
        """
        existing = (
            self.db.query(Like)
            .filter(Like.user_id == data.user_id)
            .filter(Like.target_type == data.target_type.value)
            .filter(Like.target_id == data.target_id)
            .first()
        )

        if not existing:
            raise NotLikedError(data.user_id, data.target_type, data.target_id)

        if existing.deleted_at is not None:
            # 已经取消过
            raise NotLikedError(
                data.user_id, data.target_type, data.target_id,
                message=f"user {data.user_id} has already cancelled like "
                        f"on target_type={data.target_type} target_id={data.target_id}",
            )

        with transaction(self.db):
            existing.deleted_at = now_utc8()
        return True
