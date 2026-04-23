from typing import Dict, Optional, Union

from app.schemas.v2.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    BatchUsersOut,
    UserPasswordUpdate,
)
from app.schemas.v2.user_stats import UserStatsWithUserOut

from app.storage.v2.user.user_interface import IUserRepository
from app.storage.v2.user_stats.user_stats_interface import IUserStatsRepository

from app.core.logx import logger
from app.core.exceptions import UserNotFound, PasswordMismatchError, AdminPermissionDenied
from app.core.security import hash_password, verify_password


class UserService:
    def __init__(self, user_repo: IUserRepository, stats_repo: IUserStatsRepository):
        self._user_repo = user_repo
        self._stats_repo = stats_repo

    def _hash_password(self, password: str) -> str:
        return hash_password(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    def _get_user_or_raise(self, uid: str) -> UserOut:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        return user

    def _log_operation(self, operation: str, details: str) -> None:
        logger.info(f"[{operation}] {details}")

    def _verify_admin(self, admin_uid: str) -> None:
        user = self._user_repo.find_user(uid=admin_uid)
        if not user:
            raise UserNotFound(f"admin user {admin_uid} not found")
        if user.role != 2:
            raise AdminPermissionDenied(f"User {admin_uid} is not an admin")

    def create_user(self, user_data: UserCreate, to_dict: bool = True) -> Union[Dict, UserOut]:
        if user_data.password:
            hashed = self._hash_password(user_data.password)
            user_data.password = hashed

        new_user = self._user_repo.create_user(user_data)
        self._log_operation("CREATE_USER", f"Created user uid={new_user.uid}")

        self._stats_repo.get_or_create_stats(new_user.uid)
        self._log_operation("CREATE_USER", f"Initialized statistics for user uid={new_user.uid}")

        return new_user.model_dump() if to_dict else new_user

    def get_batch_users(
        self,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True
    ) -> Union[Dict, BatchUsersOut]:
        result = self._user_repo.list_users(page=page, page_size=page_size)
        return result.model_dump() if to_dict else result

    def get_users_by_username(
        self,
        username: str,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True
    ) -> Union[Dict, BatchUsersOut]:
        result = self._user_repo.list_users(username=username, page=page, page_size=page_size)
        return result.model_dump() if to_dict else result

    def get_user_by_uid(self, uid: str, to_dict: bool = True) -> Union[Dict, UserOut]:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        return user.model_dump() if to_dict else user

    def get_user_by_phone(self, phone: str, to_dict: bool = True) -> Union[Dict, UserOut]:
        user = self._user_repo.find_user(phone=phone)
        if not user:
            raise UserNotFound(f"user with phone {phone} not found")
        return user.model_dump() if to_dict else user

    def get_user_profile(
        self,
        uid: str,
        to_dict: bool = True
    ) -> Union[Dict, UserStatsWithUserOut]:
        profile = self._stats_repo.find_stats(uid, with_user=True)
        if not profile:
            raise UserNotFound(f"user {uid} not found")
        return profile.model_dump() if to_dict else profile

    def update_user(
        self,
        uid: str,
        data: UserUpdate,
        to_dict: bool = True
    ) -> Optional[Union[Dict, UserOut]]:
        updated = self._user_repo.update_user(uid, user_info=data.user_info)
        if not updated:
            return None
        return updated.model_dump() if to_dict else updated

    def change_password(self, uid: str, data: UserPasswordUpdate) -> bool:
        stored_password = self._user_repo.get_password(uid)
        if not stored_password:
            raise UserNotFound(f"user {uid} not found")
        if not self._verify_password(data.old_password, stored_password):
            raise PasswordMismatchError()

        if data.new_password:
            hashed = self._hash_password(data.new_password)
            self._user_repo.update_user(uid, password=hashed)
        return True

    def soft_delete_user(self, uid: str) -> bool:
        result = self._user_repo.update_user(uid, deleted_at=True)
        if result:
            self._log_operation("SOFT_DELETE", f"Soft deleted user uid={uid}")
        return result is not None

    def hard_delete_user(self, admin_uid: str, user_uid: str) -> bool:
        self._verify_admin(admin_uid)
        ok = self._user_repo.delete_user(user_uid)
        if ok:
            self._log_operation("HARD_DELETE", f"Hard deleted user uid={user_uid} by admin {admin_uid}")
        return ok

    def ban_user_by_uid(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        updated = self._user_repo.update_user(user_uid, status=1)
        if not updated:
            return None
        self._log_operation("BAN_USER", f"Banned user uid={user_uid} by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated

    def frozen_user_by_uid(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        updated = self._user_repo.update_user(user_uid, status=2)
        if not updated:
            return None
        self._log_operation("FROZEN_USER", f"Frozen user uid={user_uid} by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated

    def user_to_admin(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        updated = self._user_repo.update_user(user_uid, role=2)
        if not updated:
            return None
        self._log_operation("PROMOTE_ADMIN", f"Promoted user {user_uid} to admin by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated

    def user_to_moderator(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        updated = self._user_repo.update_user(user_uid, role=1)
        if not updated:
            return None
        self._log_operation("PROMOTE_MODERATOR", f"Promoted user {user_uid} to moderator by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated