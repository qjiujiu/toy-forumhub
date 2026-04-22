import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.schemas.user import (
    UserCreate, UserOut, UserAllOut, UserDetailOut, BatchUsersOut,
    UserUpdate, AdminUserUpdate, BatchUsersAllOut
)
from app.schemas.user_stats import (
    UserStatsOut, UserStatsWithUserOut, UserStatsUpdate
)
from app.models.user import UserRole, UserStatus

class MockUserRepository:
    def __init__(self):
        self.users: Dict[str, UserAllOut] = {}

    def _to_user_out(self, user: UserAllOut) -> UserOut:
        return UserOut(
            uid=user.uid,
            username=user.username,
            avatar_url=user.avatar_url,
            role=user.role,
            bio=user.bio,
            status=user.status
        )

    def get_user_by_uid(self, uid: str) -> Optional[UserAllOut]:
        user = self.users.get(uid)
        if user and not user.deleted_at:
            return user
        return None

    def get_user_detail_by_uid(self, uid: str) -> Optional[UserDetailOut]:
        user = self.get_user_by_uid(uid)
        if user:
            return UserDetailOut.model_validate(user.model_dump())
        return None

    def get_user_by_phone(self, phone: str) -> Optional[UserOut]:
        for u in self.users.values():
            if u.phone == phone and not u.deleted_at:
                return self._to_user_out(u)
        return None

    def get_users_by_username(self, username: str, page: int, page_size: int) -> BatchUsersOut:
        matched = [self._to_user_out(u) for u in self.users.values() if u.username == username and not u.deleted_at]
        start = page * page_size
        end = start + page_size
        return BatchUsersOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def get_batch_users(self, page: int, page_size: int) -> BatchUsersOut:
        matched = [self._to_user_out(u) for u in self.users.values() if not u.deleted_at]
        start = page * page_size
        end = start + page_size
        return BatchUsersOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def create_user(self, user_data: UserCreate) -> UserOut:
        uid = str(uuid.uuid4())
        new_user = UserAllOut(
            uid=uid,
            username=user_data.username,
            phone=user_data.phone,
            email=user_data.email,
            avatar_url=user_data.avatar_url,
            bio=user_data.bio,
            password=user_data.password,
            role=user_data.role or UserRole.NORMAL_USER,
            status=user_data.status or UserStatus.NORMAL,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.users[uid] = new_user
        return self._to_user_out(new_user)

    def update_user(self, uid: str, user_data: UserUpdate) -> Optional[UserOut]:
        user = self.get_user_by_uid(uid)
        if not user:
            return None
        update_data = user_data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(user, k, v)
        user.updated_at = datetime.now()
        return self._to_user_out(user)

    def admin_update_user(self, uid: str, user_data: AdminUserUpdate) -> Optional[UserOut]:
        user = self.users.get(uid)
        if not user:
            return None
        update_data = user_data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(user, k, v)
        user.updated_at = datetime.now()
        return self._to_user_out(user)

    def update_password(self, uid: str, new_password_hash: str) -> bool:
        user = self.get_user_by_uid(uid)
        if not user:
            return False
        user.password = new_password_hash
        user.updated_at = datetime.now()
        return True

    def soft_delete_user(self, uid: str) -> bool:
        user = self.get_user_by_uid(uid)
        if not user:
            return False
        user.deleted_at = datetime.now()
        return True

    def hard_delete_user(self, uid: str) -> bool:
        if uid in self.users:
            del self.users[uid]
            return True
        return False

    def admin_get_users(self, page: int, page_size: int) -> BatchUsersAllOut:
        matched = list(self.users.values())
        start = page * page_size
        end = start + page_size
        return BatchUsersAllOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def admin_get_user_by_uid(self, uid: str) -> Optional[UserAllOut]:
        return self.users.get(uid)

    def admin_get_users_by_username(self, username: str, page: int, page_size: int) -> BatchUsersAllOut:
        matched = [u for u in self.users.values() if u.username == username]
        start = page * page_size
        end = start + page_size
        return BatchUsersAllOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def admin_list_deleted_users(self, page: int, page_size: int) -> BatchUsersAllOut:
        matched = [u for u in self.users.values() if u.deleted_at is not None]
        start = page * page_size
        end = start + page_size
        return BatchUsersAllOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def admin_list_abnormal_status_users(self, page: int, page_size: int) -> BatchUsersAllOut:
        matched = [u for u in self.users.values() if u.status != UserStatus.NORMAL]
        start = page * page_size
        end = start + page_size
        return BatchUsersAllOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

class MockUserStatsRepository:
    def __init__(self, user_repo: MockUserRepository):
        self.stats: Dict[str, UserStatsOut] = {}
        self.user_repo = user_repo

    def get_by_user_id(self, user_id: str) -> Optional[UserStatsOut]:
        return self.stats.get(user_id)

    def get_with_user_by_user_id(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        stat = self.get_by_user_id(user_id)
        if not stat:
            return None
        user_all = self.user_repo.get_user_by_uid(user_id)
        if not user_all:
            return None
        user_out = self.user_repo._to_user_out(user_all)
        return UserStatsWithUserOut(
            user=user_out,
            following_count=stat.following_count,
            followers_count=stat.followers_count
        )

    def create_for_user(self, user_id: str) -> UserStatsOut:
        if user_id not in self.stats:
            self.stats[user_id] = UserStatsOut(
                user_id=user_id,
                following_count=0,
                followers_count=0
            )
        return self.stats[user_id]

    def update_statistics(self, user_id: str, data: UserStatsUpdate) -> Optional[UserStatsOut]:
        stat = self.get_by_user_id(user_id)
        if not stat:
            return None
        if data.following_count is not None:
            stat.following_count = data.following_count
        if data.followers_count is not None:
            stat.followers_count = data.followers_count
        return stat

    def update_following(self, user_id: str, step: int = 1) -> UserStatsOut:
        stat = self.get_by_user_id(user_id)
        if not stat:
            stat = self.create_for_user(user_id)
        stat.following_count += step
        return stat

    def update_followers(self, user_id: str, step: int = 1) -> UserStatsOut:
        stat = self.get_by_user_id(user_id)
        if not stat:
            stat = self.create_for_user(user_id)
        stat.followers_count += step
        return stat

    def delete_by_user_id(self, user_id: str) -> bool:
        if user_id in self.stats:
            del self.stats[user_id]
            return True
        return False
