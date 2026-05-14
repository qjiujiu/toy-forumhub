"""
聚合仓储风格的 MockUserRepository。

物理上 users / user_stats 是两张独立表，
本 Mock 用一个对象内部维护两份字典，屏蔽多表细节，
对外以"一个用户聚合"的形式提供读写能力，对齐 IUserRepository 协议。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from app.schemas.v2.user import (
    UserCreate,
    UserOut,
    UserInfoDto,
    UserTimeDto,
    BatchUsersOut,
    UserUpdateDto,
)
from app.schemas.v2.user_stats import UserStatsDto, UserStatsWithUserOut
from app.models.v2.user import UserRole, UserStatus


def _now():
    return datetime.now(timezone(timedelta(hours=8)))


class MockUserRepository:
    """Mock 聚合仓储：内部维护 users/passwords/stats 三份字典，对外以聚合方式操作。"""

    def __init__(self):
        self.users: Dict[str, UserOut] = {}
        self.passwords: Dict[str, str] = {}
        self.stats: Dict[str, UserStatsDto] = {}

    @classmethod
    def empty(cls):
        """返回一个空仓库（无预置数据），方便单测从零开始。"""
        return cls()

    def get_password(self, uid: str) -> Optional[str]:
        return self.passwords.get(uid)

    def _base_query(self):
        return [
            u for u in self.users.values()
            if u.user_data.deleted_at is None and u.user_info.status == UserStatus.NORMAL
        ]

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        if uid:
            user = self.users.get(uid)
            if user and user.user_data.deleted_at is None and user.user_info.status == UserStatus.NORMAL:
                return user
            return None
        elif phone:
            for u in self._base_query():
                if u.user_info.phone == phone:
                    return u
            return None
        return None

    def list_users(
        self,
        username: Optional[str] = None,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        matched = self._base_query()
        if username:
            matched = [u for u in matched if u.user_info.username == username]
        matched.sort(key=lambda x: x.user_data.created_at or _now(), reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchUsersOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def create_user(self, user_data: UserCreate) -> UserOut:
        uid = str(uuid.uuid4())
        now = _now()
        new_user = UserOut(
            uid=uid,
            user_info=UserInfoDto(
                username=user_data.username,
                phone=user_data.phone,
                role=UserRole.NORMAL_USER,
                status=UserStatus.NORMAL,
            ),
            user_data=UserTimeDto(
                created_at=now,
                updated_at=now,
            ),
        )
        self.users[uid] = new_user
        self.passwords[uid] = user_data.password
        # 创建用户时自动创建统计记录（聚合不变量）
        self.stats[uid] = UserStatsDto(following_count=0, followers_count=0)
        return new_user

    def update_user(self, uid: str, update_dto: UserUpdateDto) -> Optional[UserOut]:
        user = self.users.get(uid)
        if not user or user.user_data.deleted_at or user.user_info.status != UserStatus.NORMAL:
            return None

        now = _now()
        if update_dto.user_info is not None:
            ui = update_dto.user_info
            if ui.username is not None:
                user.user_info.username = ui.username
            if ui.phone is not None:
                user.user_info.phone = ui.phone
            if ui.email is not None:
                user.user_info.email = ui.email
            if ui.avatar_url is not None:
                user.user_info.avatar_url = ui.avatar_url
            if ui.bio is not None:
                user.user_info.bio = ui.bio
            if ui.role is not None:
                user.user_info.role = ui.role
            if ui.status is not None:
                user.user_info.status = ui.status

        if update_dto.user_data is not None:
            ud = update_dto.user_data
            if ud.last_login_at is not None:
                user.user_data.last_login_at = ud.last_login_at
            if ud.created_at is not None:
                user.user_data.created_at = ud.created_at
            if ud.updated_at is not None:
                user.user_data.updated_at = ud.updated_at
            if ud.deleted_at is not None:
                user.user_data.deleted_at = ud.deleted_at

        if update_dto.password is not None:
            self.passwords[uid] = update_dto.password

        user.user_data.updated_at = now
        return user

    def delete_user(self, uid: str) -> bool:
        if uid in self.users:
            del self.users[uid]
            self.passwords.pop(uid, None)
            self.stats.pop(uid, None)
            return True
        return False

    # ========== 聚合能力：user_stats ==========

    def get_stats(self, user_id: str) -> UserStatsDto:
        stats = self.stats.get(user_id)
        if stats is None:
            raise RuntimeError(
                f"user_stats missing for user_id={user_id}; "
                f"this violates aggregate invariant."
            )
        return stats

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> UserStatsDto:
        if following_step == 0 and followers_step == 0:
            return self.get_stats(user_id)

        stats = self.stats.get(user_id)
        if stats is None:
            raise RuntimeError(
                f"user_stats missing for user_id={user_id}; cannot update stats."
            )

        if following_step != 0:
            stats.following_count = max(0, stats.following_count + following_step)
        if followers_step != 0:
            stats.followers_count = max(0, stats.followers_count + followers_step)
        return stats

    def get_user_profile(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        user = self.find_user(uid=user_id)
        if not user:
            return None
        stats = self.get_stats(user_id)
        return UserStatsWithUserOut(user_info=user, user_stats=stats)
