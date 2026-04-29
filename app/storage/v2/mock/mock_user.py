import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from app.schemas.v2.user import (
    UserCreate, UserOut, UserInfoDto, UserTimeDto, BatchUsersOut, UserUpdateDto,
)
from app.schemas.v2.user_stats import UserStatsDto, UserStatsWithUserOut
from app.models.v2.user import UserRole, UserStatus


class MockUserRepository:
    def __init__(self):
        self.users: Dict[str, UserOut] = {}
        self.passwords: Dict[str, str] = {}

    def get_password(self, uid: str) -> Optional[str]:
        return self.passwords.get(uid)

    def _base_query(self):
        return [u for u in self.users.values() if not u.user_data.deleted_at and u.user_info.status == UserStatus.NORMAL]

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        if uid:
            user = self.users.get(uid)
            if user and not user.user_data.deleted_at and user.user_info.status == UserStatus.NORMAL:
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
        matched.sort(key=lambda x: x.user_data.created_at, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchUsersOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def create_user(self, user_data: UserCreate) -> UserOut:
        uid = str(uuid.uuid4())
        now = datetime.now(timezone(timedelta(hours=8)))
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
        return new_user

    def update_user(self, uid: str, update_dto: UserUpdateDto) -> Optional[UserOut]:
        user = self.users.get(uid)
        if not user or user.user_data.deleted_at or user.user_info.status != UserStatus.NORMAL:
            return None

        now = datetime.now(timezone(timedelta(hours=8)))

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
            if uid in self.passwords:
                del self.passwords[uid]
            return True
        return False


class MockUserStatsRepository:
    def __init__(self, user_repo: MockUserRepository):
        self.stats: Dict[str, UserStatsDto] = {}
        self.user_repo = user_repo

    def find_stats(self, user_id: str, with_user: bool = False) -> Optional[UserStatsWithUserOut]:
        stat = self.stats.get(user_id)
        if not stat:
            return None

        if with_user:
            user = self.user_repo.find_user(uid=user_id)
            if not user:
                return None
            return UserStatsWithUserOut(
                user_info=user,
                user_stats=stat
            )
        return UserStatsWithUserOut(
            user_info=UserOut(uid=user_id, user_info=UserInfoDto(), user_data=UserTimeDto()),
            user_stats=stat
        )

    def get_or_create_stats(self, user_id: str) -> UserStatsDto:
        if user_id not in self.stats:
            self.stats[user_id] = UserStatsDto(
                following_count=0,
                followers_count=0
            )
        return self.stats[user_id]

    def create_for_user(self, user_id: str) -> UserStatsDto:
        return self.get_or_create_stats(user_id)

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> Optional[UserStatsDto]:
        if following_step == 0 and followers_step == 0:
            return self.get_or_create_stats(user_id)

        stat = self.stats.get(user_id)
        if stat is None:
            if following_step > 0 or followers_step > 0:
                stat = UserStatsDto(following_count=0, followers_count=0)
                self.stats[user_id] = stat
            else:
                return None

        if following_step != 0:
            stat.following_count = max(0, stat.following_count + following_step)
        if followers_step != 0:
            stat.followers_count = max(0, stat.followers_count + followers_step)
        return stat

    def delete_stats(self, user_id: str) -> bool:
        if user_id in self.stats:
            del self.stats[user_id]
            return True
        return False

    def get_by_user_id(self, user_id: str) -> Optional[UserStatsDto]:
        return self.stats.get(user_id)

    def update_following(self, user_id: str, step: int = 1) -> UserStatsDto:
        return self.update_stats(user_id, following_step=step)

    def update_followers(self, user_id: str, step: int = 1) -> UserStatsDto:
        return self.update_stats(user_id, followers_step=step)

    def delete_by_user_id(self, user_id: str) -> bool:
        return self.delete_stats(user_id)