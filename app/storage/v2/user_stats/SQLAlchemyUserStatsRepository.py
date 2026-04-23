from typing import Optional
from sqlalchemy.orm import Session
from app.models.user_stats import UserStats
from app.models.user import User, UserRole, UserStatus
from app.schemas.v2.user_stats import (
    UserStatsDto,
    UserStatsWithUserOut,
)
from app.schemas.v2.user import UserDto, UserOut
from app.storage.v2.user_stats.user_stats_interface import IUserStatsRepository
from app.core.db import transaction


def _map_stats_to_dto(stats: UserStats) -> UserStatsDto:
    return UserStatsDto(
        following_count=stats.following_count,
        followers_count=stats.followers_count,
    )


def _map_user_to_out(user: User) -> UserOut:
    return UserOut(
        uid=user.uid,
        user_info=UserDto(
            username=user.username,
            phone=user.phone,
            email=user.email,
            avatar_url=user.avatar_url,
            bio=user.bio,
        ),
        role=user.role,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        deleted_at=user.deleted_at,
    )


class SQLAlchemyUserStatsRepository(IUserStatsRepository):
    def __init__(self, db: Session):
        self.db = db

    def _get_stats_orm(self, user_id: str):
        return self.db.query(UserStats).filter(UserStats.user_id == user_id).first()

    def find_stats(self, user_id: str, with_user: bool = False) -> Optional[UserStatsWithUserOut]:
        stats = self._get_stats_orm(user_id)
        if not stats:
            return None

        if with_user:
            user = self.db.query(User).filter(
                User.uid == user_id,
                User.deleted_at.is_(None),
                User.status == 0,
            ).first()
            if not user:
                return None
            return UserStatsWithUserOut(
                user_info=_map_user_to_out(user),
                user_stats=_map_stats_to_dto(stats),
            )
        return UserStatsWithUserOut(
            user_info=UserOut(uid=user_id, user_info=UserDto(username="", phone="")),
            user_stats=_map_stats_to_dto(stats),
        )

    def get_or_create_stats(self, user_id: str) -> UserStatsDto:
        stats = self._get_stats_orm(user_id)
        if stats is None:
            stats = UserStats(user_id=user_id, following_count=0, followers_count=0)
            with transaction(self.db):
                self.db.add(stats)
            self.db.refresh(stats)
        return _map_stats_to_dto(stats)

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> Optional[UserStatsDto]:
        if following_step == 0 and followers_step == 0:
            return self.get_or_create_stats(user_id)

        stats = self._get_stats_orm(user_id)
        if stats is None:
            if following_step > 0 or followers_step > 0:
                stats = UserStats(user_id=user_id, following_count=0, followers_count=0)
                with transaction(self.db):
                    self.db.add(stats)
            else:
                return None

        with transaction(self.db):
            if following_step != 0:
                stats.following_count = max(0, stats.following_count + following_step)
            if followers_step != 0:
                stats.followers_count = max(0, stats.followers_count + followers_step)

        self.db.refresh(stats)
        return _map_stats_to_dto(stats)

    def delete_stats(self, user_id: str) -> bool:
        stats = self._get_stats_orm(user_id)
        if stats is None:
            return False
        with transaction(self.db):
            self.db.delete(stats)
        return True