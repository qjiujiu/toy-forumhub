from typing import Optional, List
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.follow import Follow
from app.models.user import User
from app.schemas.follow import (
    FollowCreate,
    FollowOut,
    FollowUserOut,
    BatchFollowsOut,
    FollowCancel,
    FollowAdminOut,
)
from app.schemas.user import UserOut
from app.storage.follow.follow_interface import IFollowRepository
from app.core.db import transaction
from app.core.logx import logger
logger.is_debug(True)

class SQLAlchemyFollowRepository(IFollowRepository):
    """
    使用 SQLAlchemy 实现的关注关系仓库
    """

    def __init__(self, db: Session):
        self.db = db

    def _active_query(self):
        """只查询未软删除的关注记录"""
        return self.db.query(Follow).filter(Follow.deleted_at.is_(None))

    def create_follow(self, data: FollowCreate) -> FollowOut:
        """
        创建关注：
        - 如果已存在软删除的记录 => 视为重新关注：deleted_at 置空，created_at 更新为现在
        - 如果已存在未删除记录 => 直接返回
        """
        # 先查是否已有记录（无论软删与否）
        existing = (
            self.db.query(Follow)
            .filter(
                Follow.user_id == data.user_id,
                Follow.followed_user_id == data.followed_user_id,
            )
            .first()
        )

        now = datetime.now(timezone(timedelta(hours=8)))

        if existing:
            # 已存在 soft-deleted，则视为重新关注
            if existing.deleted_at is not None:
                with transaction(self.db):
                    existing.deleted_at = None
                    existing.created_at = now
                self.db.refresh(existing)
            # 已有有效记录，直接返回
            return FollowOut.model_validate(existing)

        # 不存在任何记录，则新建
        follow = Follow(
            user_id=data.user_id,
            followed_user_id=data.followed_user_id,
            created_at=now,
            deleted_at=None,
        )

        with transaction(self.db):
            self.db.add(follow)

        self.db.refresh(follow)
        return FollowOut.model_validate(follow)

    def cancel_follow(self, data: FollowCancel) -> bool:
        """
        取消关注（软删除）
        """
        follow = (
            self._active_query()
            .filter(
                Follow.user_id == data.user_id,
                Follow.followed_user_id == data.followed_user_id,
            )
            .first()
        )
        if not follow:
            return False

        with transaction(self.db):
            follow.deleted_at = datetime.now(timezone(timedelta(hours=8)))

        return True

    def hard_delete_follow(self, user_id: str, followed_user_id: str) -> bool:
        """
        硬删除关注记录：
        - 不关心 deleted_at 状态，直接删除这两个人之间的关注关系
        - 如果不存在记录，返回 False
        """
        follow: Optional[Follow] = (
            self.db.query(Follow)
            .filter(
                Follow.user_id == user_id,
                Follow.followed_user_id == followed_user_id,
            )
            .first()
        )

        if not follow:
            return False

        with transaction(self.db):
            self.db.delete(follow)

        return True

    def hard_delete_all_by_user(self, user_id: str) -> int:
        """
        删除与某个用户相关的所有关注记录（双向）
        - 包含 user_id 为关注者，或 followed_user_id 为被关注者
        """
        q = self.db.query(Follow).filter(
            or_(
                Follow.user_id == user_id,
                Follow.followed_user_id == user_id,
            )
        )
        count = q.count()
        if count == 0:
            return 0

        with transaction(self.db):
            q.delete(synchronize_session=False)

        return count

    def get_follow(self, user_id: str, followed_user_id: str) -> Optional[FollowOut]:
        """
        用户获取有效的关注关系
        """
        follow = (
            self._active_query()
            .filter(
                Follow.user_id == user_id,
                Follow.followed_user_id == followed_user_id,
            )
            .first()
        )
        return FollowOut.model_validate(follow) if follow else None

    def admin_get_follow(self, user_id: str, followed_user_id: str) -> Optional[FollowAdminOut]:
        """
        管理员获取关注关系
        """
        follow = (
            self.db.query(Follow)
            .filter(
                Follow.user_id == user_id,
                Follow.followed_user_id == followed_user_id,
            )
            .first()
        )
        return FollowAdminOut.model_validate(follow) if follow else None

    def is_following(self, user_id: str, followed_user_id: str) -> bool:
        """
        判断是否正在关注
        """
        return (
            self._active_query()
            .filter(
                Follow.user_id == user_id,
                Follow.followed_user_id == followed_user_id,
            )
            .first()
            is not None
        )


    def list_following(self, user_id: str, page: int, page_size: int) -> BatchFollowsOut:
        """
        我关注的人列表：
        - 从 Follow 中找出 user_id = 当前用户 的记录
        - join 到 User 表拿到被关注者的用户信息
        - 再计算这些人中，哪些也关注了我（互关）
        """

        base_q = (
            self.db.query(Follow, User)
            .join(User, User.uid == Follow.followed_user_id)
            .filter(
                Follow.user_id == user_id,
                Follow.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
            .order_by(Follow.created_at.desc())
        )

        total = base_q.count()

        rows = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        # 对方用户 ID 列表，用于批量查询互关
        other_user_ids = [u.uid for _, u in rows]

        mutual_ids = self._get_mutual_ids_following(
            user_id=user_id,
            other_user_ids=other_user_ids,
        )

        items: List[FollowUserOut] = []
        for _, user_orm in rows:
            user_out = UserOut.model_validate(user_orm)
            items.append(
                FollowUserOut(
                    user=user_out,
                    is_mutual=(user_orm.uid in mutual_ids),
                )
            )

        return BatchFollowsOut(
            total=total,
            count=len(items),
            items=items,
        )

    def list_followers(self, user_id: str, page: int, page_size: int) -> BatchFollowsOut:
        """
        我的粉丝列表：
        - 从 Follow 中找出 followed_user_id = 当前用户 的记录
        - join 到 User 表拿到关注者的用户信息
        - 再计算这些人中，哪些也是我关注的（互关）
        """
        logger.debug("ok")
        base_q = (
            self.db.query(Follow, User)
            .join(User, User.uid == Follow.user_id)
            .filter(
                Follow.followed_user_id == user_id,
                Follow.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
            .order_by(Follow.created_at.desc())
        )

        total = base_q.count()

        rows = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        other_user_ids = [u.uid for _, u in rows]

        # for f, u in rows:
        #     logger.debug(f"user_id={f.user_id}, followed_user_id={f.followed_user_id}, u.uid={u.uid}")

        mutual_ids = self._get_mutual_ids_followers(
            user_id=user_id,
            other_user_ids=other_user_ids,
        )
        # logger.debug(f"mutual_ids: {mutual_ids}")
        
        items: List[FollowUserOut] = []
        for _, user_orm in rows:
            user_out = UserOut.model_validate(user_orm)
            items.append(
                FollowUserOut(
                    user=user_out,
                    is_mutual=(user_orm.uid in mutual_ids),
                )
            )

        return BatchFollowsOut(
            total=total,
            count=len(items),
            items=items,
        )

    def _get_mutual_ids_following(self, user_id: str, other_user_ids: List[str]) -> set[str]:
        """
        list_following 用：
        - 判断 other_user_ids（我关注的人）是否也关注我
        """
        if not other_user_ids:
            return set()
        rows = (
            self._active_query()
            .filter(
                Follow.user_id.in_(other_user_ids),
                Follow.followed_user_id == user_id,
            )
            .all()
        )
        return {f.user_id for f in rows}

    def _get_mutual_ids_followers(self, user_id: str, other_user_ids: List[str]) -> set[str]:
        """
        list_followers 用：
        - 判断我是否关注 other_user_ids（我的粉丝）
        """
        if not other_user_ids:
            return set()
        rows = (
            self._active_query()
            .filter(
                Follow.user_id == user_id,
                Follow.followed_user_id.in_(other_user_ids),
            )
            .all()
        )
        return {f.followed_user_id for f in rows}
