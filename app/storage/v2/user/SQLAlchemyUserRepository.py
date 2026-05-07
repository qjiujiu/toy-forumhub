from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.v2.user import User, UserRole, UserStatus
from app.models.v2.user_stats import UserStats
from app.schemas.v2.user import (
    UserInfoDto,
    UserTimeDto,
    UserCreate,
    UserOut,
    BatchUsersOut,
    UserUpdateDto,
)
from app.schemas.v2.user_stats import UserStatsDto, UserStatsWithUserOut
from app.storage.v2.user.user_interface import IUserRepository
from app.core.db import transaction


def _to_user_out(user: User) -> UserOut:
    return UserOut(
        uid=user.uid,
        user_info=UserInfoDto.model_validate(user),
        user_data=UserTimeDto.model_validate(user),
    )


def _apply_nested_dto(user, dto, field_names: list, now: datetime = None):
    for field in field_names:
        value = getattr(dto, field, None)
        if value is not None:
            setattr(user, field, value)


def _apply_user_update(user: User, update_dto: UserUpdateDto, now: datetime):
    if update_dto.user_info is not None:
        _apply_nested_dto(user, update_dto.user_info, ["username", "phone", "email", "avatar_url", "bio", "role", "status"])

    if update_dto.user_data is not None:
        time_fields = ["last_login_at", "created_at", "updated_at", "deleted_at"]
        for field in time_fields:
            value = getattr(update_dto.user_data, field, None)
            if value is not None:
                setattr(user, field, value)
            else:
                setattr(user, field, now)

    if update_dto.password is not None:
        user.password = update_dto.password


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(User).filter(
            User.deleted_at.is_(None),
            User.status == 0,
        )

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        if uid:
            user = self._base_query().filter(User.uid == uid).first()
        elif phone:
            user = self._base_query().filter(User.phone == phone).first()
        else:
            return None
        return _to_user_out(user) if user else None

    def list_users(
        self,
        username: Optional[str] = None,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        base_q = self._base_query()
        if username:
            base_q = base_q.filter(User.username == username)
        base_q = base_q.order_by(User.created_at.desc())

        total = base_q.count()
        users_orm = base_q.offset(page * page_size).limit(page_size).all()
        users_out = [_to_user_out(u) for u in users_orm]

        return BatchUsersOut(
            total=total,
            count=len(users_out),
            users=users_out,
        )

    def create_user(self, user_data: UserCreate) -> UserOut:
        """
        创建用户聚合：一次事务内写入 users + user_stats。
        保证用户创建后必然有对应的统计记录（0/0）。
        """
        user = User(
            username=user_data.username,
            phone=user_data.phone,
            password=user_data.password,
            role=UserRole.NORMAL_USER.value,
            status=UserStatus.NORMAL.value,
        )

        # 创建默认统计记录
        stats = UserStats(user_id=user.uid, following_count=0, followers_count=0)

        with transaction(self.db):
            self.db.add_all([user, stats])

        self.db.refresh(user)
        return _to_user_out(user)

    def update_user(self, uid: str, update_dto: UserUpdateDto) -> Optional[UserOut]:
        user = self._base_query().filter(User.uid == uid).first()
        if not user:
            return None

        now = datetime.now(timezone(timedelta(hours=8)))
        with transaction(self.db):
            _apply_user_update(user, update_dto, now)

        self.db.refresh(user)
        return _to_user_out(user)

    def delete_user(self, uid: str) -> bool:
        user = self.db.query(User).filter(User.uid == uid).first()
        if not user:
            return False
        with transaction(self.db):
            self.db.delete(user)
        return True

    def get_password(self, uid: str) -> Optional[str]:
        user = self._base_query().filter(User.uid == uid).first()
        return user.password if user else None

    # ========== 聚合能力：user_stats ==========

    def _get_stats_orm(self, user_id: str):
        return self.db.query(UserStats).filter(UserStats.user_id == user_id).first()

    def get_stats(self, user_id: str) -> UserStatsDto:
        stats = self._get_stats_orm(user_id)
        if stats is None:
            raise RuntimeError(
                f"user_stats missing for user_id={user_id}; "
                f"this violates aggregate invariant (users/user_stats should be created together). "
                f"Please run a backfill/migration to repair historical data."
            )
        return UserStatsDto.model_validate(stats)

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> UserStatsDto:
        if following_step == 0 and followers_step == 0:
            return self.get_stats(user_id)

        stats = self._get_stats_orm(user_id)
        if stats is None:
            raise RuntimeError(
                f"user_stats missing for user_id={user_id}; cannot update stats. "
                f"Please repair historical data first."
            )

        with transaction(self.db):
            if following_step != 0:
                stats.following_count = max(0, stats.following_count + following_step)
            if followers_step != 0:
                stats.followers_count = max(0, stats.followers_count + followers_step)

        self.db.refresh(stats)
        return UserStatsDto.model_validate(stats)

    def get_user_profile(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        user = self._base_query().filter(User.uid == user_id).first()
        if not user:
            return None

        stats_dto = self.get_stats(user_id)

        return UserStatsWithUserOut(
            user_info=_to_user_out(user),
            user_stats=stats_dto,
        )
