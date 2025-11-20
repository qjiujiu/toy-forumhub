from typing import Optional

from sqlalchemy.orm import Session

from app.models.user_stats import UserStats
from app.models.user import User
from app.schemas.user_stats import (
    UserStatsOut,
    UserStatsWithUserOut,
    UserStatsUpdate,
)
from app.schemas.user import UserOut
from app.storage.user_stats.user_stats_interface import IUserStatsRepository
from app.core.db import transaction 

class SQLAlchemyUserStatsRepository(IUserStatsRepository):
    """
    使用 SQLAlchemy 实现的用户关注/粉丝统计仓库
    """

    def __init__(self, db: Session):
        self.db = db


    def _get_stats_orm(self, user_id: str) -> Optional[UserStats]:
        return (
            self.db.query(UserStats)
            .filter(UserStats.user_id == user_id)
            .first()
        )

    def _get_or_create_stats_orm(self, user_id: str) -> UserStats:
        """
        获取统计记录，如果不存在则创建一条默认记录并返回
        """
        stats = self._get_stats_orm(user_id)
        if stats is None:
            stats = UserStats(user_id=user_id, following_count=0, followers_count=0,)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
        return stats

    def get_by_user_id(self, user_id: str) -> Optional[UserStatsOut]:
        stats = self._get_stats_orm(user_id)
        return UserStatsOut.model_validate(stats) if stats else None

    def get_with_user_by_user_id(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        """
        join User 表，组装 UserStatsWithUserOut
        """
        # 这里假设 User.uid 与 UserStats.user_id 对应
        row = (
            self.db.query(UserStats, User)
            .join(User, User.uid == UserStats.user_id)
            .filter(UserStats.user_id == user_id)
            .first()
        )

        if not row:
            return None

        stats_orm, user_orm = row

        return UserStatsWithUserOut(
            user=UserOut.model_validate(user_orm),
            following_count=stats_orm.following_count,
            followers_count=stats_orm.followers_count,
        )

    def create_for_user(self, user_id: str) -> UserStatsOut:
        """
        创建统计记录，如果已存在则直接返回已有记录
        """
        stats = self._get_stats_orm(user_id)
        if stats is None:
            stats = UserStats(user_id=user_id, following_count=0, followers_count=0)
            with transaction(self.db):
                self.db.add(stats)

            self.db.refresh(stats)

        return UserStatsOut.model_validate(stats)

    def update_statistics(self, user_id: str, data: UserStatsUpdate) -> Optional[UserStatsOut]:
        stats = self._get_stats_orm(user_id)
        if stats is None:
            return None

        update_data = data.model_dump(exclude_none=True)

        with transaction(self.db):
            for field, value in update_data.items():
                setattr(stats, field, value)

        self.db.refresh(stats)
        return UserStatsOut.model_validate(stats)

    def update_following(self, user_id: str, step: int = 1) -> UserStatsOut:
        """
        关注数自增/自减（step 可以为负）
        """
        with transaction(self.db):
            stats = self._get_or_create_stats_orm(user_id)

            new_value = stats.following_count + step
            stats.following_count = max(new_value, 0)

        self.db.refresh(stats)
        return UserStatsOut.model_validate(stats)

    def update_followers(self, user_id: str, step: int = 1) -> UserStatsOut:
        """
        粉丝数自增/自减（step 可以为负）
        """
        with transaction(self.db):
            stats = self._get_or_create_stats_orm(user_id)

            new_value = stats.followers_count + step
            stats.followers_count = max(new_value, 0)

        self.db.refresh(stats)
        return UserStatsOut.model_validate(stats)

    def delete_by_user_id(self, user_id: str) -> bool:
        """
        硬删除统计记录（一般在用户硬删除时调用）
        """
        stats = self._get_stats_orm(user_id)
        if stats is None:
            return False

        with transaction(self.db):
            self.db.delete(stats)

        return True
