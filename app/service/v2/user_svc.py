from app.core.logx import logger
from app.core.exceptions import UserNotFound, PasswordMismatchError, AdminPermissionDenied
from app.core.security import hash_password, verify_password
from app.storage.v2.user.user_interface import IUserRepository
from app.schemas.v2.user_stats import UserStatsWithUserOut
from app.schemas.v2.user import (
    UserUpdate,
    UserOut,
    BatchUsersOut,
    UserPasswordUpdate,
    UserStatus,
    UserRole,
)

from app.schemas.v2.user_req import UserInfoPatch, UserAdminPatch, UserPasswordPatch

from typing import Optional
from datetime import datetime, timezone, timedelta


class UserService:
    """ v2 UserService
    本模块刻意强调“分层边界”一种取舍：

    1) repo 尽可能保持“原始 CRUD + 一个通用 update”
    - repo 负责把数据写进数据库, 以及维护多表写入一致性，例如 create_user 创建一个用户基本信息的时候回创建用户关注与粉丝信息 (user_stats)
    - 用户字段更新，repo 对外只暴露 `update_user(uid, patch)`，语义更接近“数据访问层”。

    2) service 承担“按意图的更新 API”（用例编排）
    - `update_user`（普通资料更新）、`change_password`（重置密码）、`soft_delete_user`（软删）、
    `ban_user_by_uid/frozen_user_by_uid`（封禁/冻结）、`user_to_admin/user_to_moderator`（角色变更）。
    - service 负责鉴权、状态机、日志等业务流程；并把“这次更新要改哪些字段”组装成 patch。

    3) 为什么 patch 需要区分 UserInfoPatch/UserAdminPatch/UserPasswordPatch 类型？
    - 如果 repo 的 update 接收一个无边界 dict/万能 DTO，普通更新很容易误改敏感字段（role/status/password/deleted_at）。
    - 区分 patch 类型相当于把“字段边界”写进类型系统，减少误用；也是一种教学用的防线。

    4) NOTE 这种设计的利弊 
    - 好处：repo 更像纯数据层，接口更稳定；新增业务意图动作通常只改 service, 无需往下逐层修改。
    - 代价：约束更依赖 service；如果将来有其它调用方绕过 service 直接使用 repo.update_user, 仍可能写出越权/不一致数据, 
    因此, 要么保证未来的所有写入口全部经过 service , 要么就在 repo/update 继续加上更强约束/审计; 我们建议采用前者。
    """

    def __init__(self, user_repo: IUserRepository):
        # UserService 只依赖一个 UserRepository（聚合仓储）。
        # 用户统计信息（user_stats）虽然是独立表，但访问细节应由 repo 层屏蔽。
        self._user_repo = user_repo

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

    def create_user(self, username: str, phone: str, password: str) -> UserOut:
        new_user = self._user_repo.create_user(
            username=username,
            phone=phone,
            hashed_password=hash_password(password)
        )

        logger.info(f"[CREATE_USER] Created user uid={new_user.uid}")
        return new_user

    def get_batch_users(
        self,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        result = self._user_repo.list_users(page=page, page_size=page_size)
        return result

    def get_users_by_username(
        self,
        username: str,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        result = self._user_repo.list_users(username=username, page=page, page_size=page_size)
        return result

    def get_user_by_uid(self, uid: str) -> UserOut:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        return user

    def get_user_by_phone(self, phone: str) -> UserOut:
        user = self._user_repo.find_user(phone=phone)
        if not user:
            raise UserNotFound(f"user with phone {phone} not found")
        return user

    def get_user_profile(
        self,
        uid: str,
    ) -> UserStatsWithUserOut:
        profile = self._user_repo.get_user_profile(uid)
        if not profile:
            raise UserNotFound(f"user {uid} not found")
        return profile

    def update_user(
        self,
        uid: str,
        data: UserUpdate,
    ) -> Optional[UserOut]:
        patch = UserInfoPatch(**data.user_info.model_dump(exclude_unset=True))
        return self._user_repo.update_user(uid, patch)

    def change_password(self, uid: str, data: UserPasswordUpdate) -> bool:
        stored_password = self._user_repo.get_password(uid)
        if not stored_password:
            raise UserNotFound(f"user {uid} not found")
        if not verify_password(data.old_password, stored_password):
            raise PasswordMismatchError()

        if data.new_password:
            patch = UserPasswordPatch(password=hash_password(data.new_password))
            is_updated = self._user_repo.update_user(uid, patch)
            if not is_updated:
                # 正常情况下不应发生：上面已经通过 get_password 校验了用户存在。
                raise UserNotFound(f"user {uid} not found")
        return True

    def soft_delete_user(self, uid: str) -> bool:
        now = datetime.now(timezone(timedelta(hours=8)))
        patch = UserAdminPatch(deleted_at=now)
        is_updated = self._user_repo.update_user(uid, patch)
        if is_updated:
            logger.info(f"[SOFT_DELETE] Soft deleted user uid={uid}")
        return is_updated is not None

    def hard_delete_user(self, admin_uid: str, user_uid: str) -> bool:
        self._verify_admin(admin_uid)
        is_ok = self._user_repo.delete_user(user_uid)
        if is_ok:
            logger.info(f"[HARD_DELETE] Hard deleted user uid={user_uid} by admin {admin_uid}")
        return is_ok

    def ban_user_by_uid(self, admin_uid: str, user_uid: str) -> Optional[UserOut]:
        self._verify_admin(admin_uid)
        is_updated = self._user_repo.update_user(user_uid, UserAdminPatch(status=UserStatus.BANNED))
        if is_updated:
            logger.info(f"[BAN_USER] Banned user uid={user_uid} by admin {admin_uid}")
        return is_updated

    def frozen_user_by_uid(self, admin_uid: str, user_uid: str) -> Optional[UserOut]:
        self._verify_admin(admin_uid)
        is_updated = self._user_repo.update_user(user_uid, UserAdminPatch(status=UserStatus.FROZEN))
        if is_updated:
            logger.info(f"[FROZEN_USER] Frozen user uid={user_uid} by admin {admin_uid}")
        return is_updated

    def user_to_admin(self, admin_uid: str, user_uid: str) -> Optional[UserOut]:
        self._verify_admin(admin_uid)
        is_updated = self._user_repo.update_user(user_uid, UserAdminPatch(role=UserRole.ADMIN))
        if is_updated:
            logger.info(f"[PROMOTE_ADMIN] Promoted user {user_uid} to admin by admin {admin_uid}")
        return is_updated

    def user_to_moderator(self, admin_uid: str, user_uid: str) -> Optional[UserOut]:
        self._verify_admin(admin_uid)
        is_updated = self._user_repo.update_user(user_uid, UserAdminPatch(role=UserRole.MODERATOR))
        if is_updated:
            logger.info(f"[PROMOTE_MODERATOR] Promoted user {user_uid} to moderator by admin {admin_uid}")
        return is_updated
