from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.follow import Follow
from app.models.v2.user import User

from app.schemas.v2.follow import (
    FollowCreate,
    FollowCancel,
    FollowDto,
    FollowOut,
    BatchFollowsOut,
)
from app.schemas.user import UserOut

from app.storage.v2.follow.follow_interface import IFollowRepository

from app.core.time import now_utc8
from app.core.db import transaction
from app.core.exceptions import AlreadyFollowingError, NotFollowingError


class SQLAlchemyFollowRepository(IFollowRepository):
    """关注数据层 SQLAlchemy 实现。"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== C ====================

    def follow(self, data: FollowCreate) -> bool:
        """
        关注用户：创建新关注或恢复已取消的关注。
        """
        existing = (
            self.db.query(Follow)
            .filter(Follow.user_id == data.user_id)
            .filter(Follow.followed_user_id == data.followed_user_id)
            .first()
        )

        if existing:
            if existing.deleted_at is None:
                raise AlreadyFollowingError(data.user_id, data.followed_user_id)
            # 恢复已取消的关注
            with transaction(self.db):
                existing.deleted_at = None
            return True

        # 全新关注
        follow = Follow(
            user_id=data.user_id,
            followed_user_id=data.followed_user_id,
        )
        with transaction(self.db):
            self.db.add(follow)
        return True

    # ==================== D ====================

    def unfollow(self, data: FollowCancel) -> bool:
        """
        取消关注（软删除）。
        """
        existing = (
            self.db.query(Follow)
            .filter(Follow.user_id == data.user_id)
            .filter(Follow.followed_user_id == data.followed_user_id)
            .first()
        )

        if not existing:
            raise NotFollowingError(data.user_id, data.followed_user_id)

        if existing.deleted_at is not None:
            raise NotFollowingError(
                data.user_id, data.followed_user_id,
                message=f"user {data.user_id} is not following {data.followed_user_id} (already unfollowed)",
            )

        with transaction(self.db):
            existing.deleted_at = now_utc8()
        return True

    def hard_unfollow(self, data: FollowCancel) -> bool:
        """
        硬删除关注记录。
        """
        existing = (
            self.db.query(Follow)
            .filter(Follow.user_id == data.user_id)
            .filter(Follow.followed_user_id == data.followed_user_id)
            .first()
        )

        if not existing:
            raise NotFollowingError(data.user_id, data.followed_user_id)

        with transaction(self.db):
            self.db.delete(existing)
        return True

    # ==================== R ====================

    def get_follows(
        self,
        query: FollowDto,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchFollowsOut:
        """
        动态字段过滤查询关注关系，自动排除软删除。
        - user_id='xxx' → 查 xxx 的关注列表
        - followed_user_id='xxx' → 查 xxx 的粉丝列表
        """
        base_q = self.db.query(Follow).filter(Follow.deleted_at.is_(None))

        for field_name in query.model_fields:
            field_value = getattr(query, field_name, None)
            if field_value is not None:
                model_field = getattr(Follow, field_name, None)
                if model_field is not None:
                    base_q = base_q.filter(model_field == field_value)

        base_q = base_q.order_by(desc(Follow._id))

        total = base_q.count()
        follow_orms = base_q.offset(page * page_size).limit(page_size).all()

        items = []
        for f in follow_orms:
            # 根据查询上下文确定要展示的"对方"用户
            # 查关注列表 → 展示被关注者；查粉丝列表 → 展示关注者
            target_user: Optional[User] = None
            if query.followed_user_id is not None and query.user_id is None:
                # 粉丝列表：展示关注者（发起关注的人）
                target_user = f.user
            else:
                # 关注列表（含两者都传的情况）：展示被关注者
                target_user = f.followed_user

            if target_user is None:
                continue

            # 检测是否互关：被关注者是否也关注了关注者
            # 即：f.followed_user 是否也有一条指向 f.user 的关注记录
            is_mutual = (
                self.db.query(Follow)
                .filter(Follow.user_id == f.followed_user_id)
                .filter(Follow.followed_user_id == f.user_id)
                .filter(Follow.deleted_at.is_(None))
                .first()
            ) is not None

            items.append(FollowOut(
                user=UserOut.model_validate(target_user),
                is_mutual=is_mutual,
            ))

        return BatchFollowsOut(total=total, count=len(items), items=items)
