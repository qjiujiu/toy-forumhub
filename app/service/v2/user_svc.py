from typing import Dict, Optional, Union
from datetime import datetime, timezone, timedelta

from app.schemas.v2.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    BatchUsersOut,
    UserPasswordUpdate,
    UserUpdateDto,
    UserInfoDto,
    UserTimeDto,
    UserStatus,
    UserRole,
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

    def _get_user_or_raise(self, uid: str) -> UserOut:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        return user

    def _verify_admin(self, admin_uid: str) -> None:
        user = self._user_repo.find_user(uid=admin_uid)
        if not user:
            raise UserNotFound(f"admin user {admin_uid} not found")
        if user.user_info.role != UserRole.ADMIN:
            raise AdminPermissionDenied(f"User {admin_uid} is not an admin")

    def create_user(self, user_data: UserCreate, to_dict: bool = True) -> Union[Dict, UserOut]:
        if user_data.password:
            user_data.password = hash_password(user_data.password)

        new_user = self._user_repo.create_user(user_data)
        logger.info(f"[CREATE_USER] Created user uid={new_user.uid}")

        self._stats_repo.get_or_create_stats(new_user.uid)
        logger.info(f"[CREATE_USER] Initialized statistics for user uid={new_user.uid}")

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
        update_dto = UserUpdateDto(user_info=UserInfoDto.model_validate(data.user_info, from_attributes=True))
        updated = self._user_repo.update_user(uid, update_dto)
        if not updated:
            return None
        return updated.model_dump() if to_dict else updated

    def change_password(self, uid: str, data: UserPasswordUpdate) -> bool:
        stored_password = self._user_repo.get_password(uid)
        if not stored_password:
            raise UserNotFound(f"user {uid} not found")
        if not verify_password(data.old_password, stored_password):
            raise PasswordMismatchError()

        if data.new_password:
            update_dto = UserUpdateDto(password=hash_password(data.new_password))
            self._user_repo.update_user(uid, update_dto)
        return True

    def soft_delete_user(self, uid: str) -> bool:
        now = datetime.now(timezone(timedelta(hours=8)))
        update_dto = UserUpdateDto(user_data=UserTimeDto(deleted_at=now))
        result = self._user_repo.update_user(uid, update_dto)
        if result:
            logger.info(f"[SOFT_DELETE] Soft deleted user uid={uid}")
        return result is not None

    def hard_delete_user(self, admin_uid: str, user_uid: str) -> bool:
        self._verify_admin(admin_uid)
        ok = self._user_repo.delete_user(user_uid)
        if ok:
            logger.info(f"[HARD_DELETE] Hard deleted user uid={user_uid} by admin {admin_uid}")
        return ok

    def ban_user_by_uid(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        update_dto = UserUpdateDto(user_info=UserInfoDto(status=UserStatus.BANNED))
        updated = self._user_repo.update_user(user_uid, update_dto)
        if not updated:
            return None
        logger.info(f"[BAN_USER] Banned user uid={user_uid} by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated

    def frozen_user_by_uid(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        update_dto = UserUpdateDto(user_info=UserInfoDto(status=UserStatus.FROZEN))
        updated = self._user_repo.update_user(user_uid, update_dto)
        if not updated:
            return None
        logger.info(f"[FROZEN_USER] Frozen user uid={user_uid} by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated

    def user_to_admin(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        update_dto = UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN))
        updated = self._user_repo.update_user(user_uid, update_dto)
        if not updated:
            return None
        logger.info(f"[PROMOTE_ADMIN] Promoted user {user_uid} to admin by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated

    def user_to_moderator(self, admin_uid: str, user_uid: str, to_dict: bool = True) -> Optional[Union[Dict, UserOut]]:
        self._verify_admin(admin_uid)
        update_dto = UserUpdateDto(user_info=UserInfoDto(role=UserRole.MODERATOR))
        updated = self._user_repo.update_user(user_uid, update_dto)
        if not updated:
            return None
        logger.info(f"[PROMOTE_MODERATOR] Promoted user {user_uid} to moderator by admin {admin_uid}")
        return updated.model_dump() if to_dict else updated