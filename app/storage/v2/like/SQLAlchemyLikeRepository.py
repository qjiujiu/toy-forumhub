import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.dialects.mysql import insert as mysql_insert
from app.models.v2.like import Like

from app.schemas.v2.like import (
    LikeCreate,
    LikeCancel,
    LikeDto,
    LikeOut,
    BatchLikesOut,
)

from app.storage.v2.like.like_interface import ILikeRepository

from app.kit.time import now_utc8
from app.core.db import transaction
from app.kit.exceptions import AlreadyLikedError, NotLikedError

logger = logging.getLogger(__name__)


class SQLAlchemyLikeRepository(ILikeRepository):
    """点赞数据层 SQLAlchemy 实现。"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== C ====================

    def create_or_restore(self, data: LikeCreate) -> LikeOut:
        """
        创建新点赞或恢复已取消的点赞。
        利用 UNIQUE 约束 + UPSERT 原子性防止并发重复，无需悲观锁。

        MySQL rowcount 语义：
        - 1: 新插入（全新点赞）
        - 2: 更新了已有行（从软删除恢复）
        - 0: 行无变化（已点赞未取消 → 幂等拒绝）
        """
        now = now_utc8()
        stmt = mysql_insert(Like).values(
            lid=str(uuid.uuid4()),
            user_id=data.user_id,
            target_type=data.target_type.value,
            target_id=data.target_id,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        ).on_duplicate_key_update(
            deleted_at=None,
            # 不更新 updated_at，以此判断是否真实变化：
            # deleted_at 已为 NULL → 无变化 → rowcount=0
            # deleted_at 非 NULL → 恢复 → rowcount=2
        )

        with transaction(self.db):
            result = self.db.execute(stmt)

        if result.rowcount == 0:
            raise AlreadyLikedError(data.user_id, data.target_type, data.target_id)

        like = (
            self.db.query(Like)
            .filter(Like.user_id == data.user_id)
            .filter(Like.target_type == data.target_type.value)
            .filter(Like.target_id == data.target_id)
            .first()
        )
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
