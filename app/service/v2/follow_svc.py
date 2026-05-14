from typing import Union, Dict

from app.models.v2.user import UserStatus
from app.schemas.v2.follow import (
    FollowCreate,
    FollowCancel,
    FollowDto,
    FollowOut,
    BatchFollowsOut,
)
from app.schemas.v2.user import UserRole

from app.storage.v2.follow.follow_interface import IFollowRepository
from app.storage.v2.user.user_interface import IUserRepository

import logging
logger = logging.getLogger(__name__)
from app.kit.exceptions import (
    FollowYourselfError,
    ForbiddenAction,
    UserNotFound,
    AdminPermissionDenied,
    HardDeleteFollowRequiresSoftDeleteError,
)


class FollowService:
    """
    关注业务层。

    - 创建/取消关注时同步更新双方的 following_count / followers_count。
    - 关注数更新通过 user_repo.update_stats() 增量语义，计数不下溢。
    """

    def __init__(
        self,
        follow_repo: IFollowRepository,
        user_repo: IUserRepository,
    ):
        self._follow_repo = follow_repo
        self._user_repo = user_repo

    def _get_user_or_raise(self, uid: str) -> None:
        """验证用户存在，不存在则抛 UserNotFound。"""
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(user_id=uid)
        if user.user_info.status != UserStatus.NORMAL:
            raise ForbiddenAction(f"user {uid} is not active (status={user.user_info.status})")

    def _verify_admin(self, admin_uid: str) -> None:
        """验证操作者是否为管理员。"""
        user = self._user_repo.find_user(uid=admin_uid)
        if not user:
            raise UserNotFound(user_id=admin_uid)
        if user.user_info.role != UserRole.ADMIN:
            raise AdminPermissionDenied(f"user {admin_uid} is not an admin")

    # ==================== C ====================

    def follow(self, data: FollowCreate) -> bool:
        """
        关注用户。

        流程：
        1. 校验关注者和被关注者都存在
        2. 禁止关注自己
        3. 调用数据层创建关注（可能抛 AlreadyFollowingError）
        4. 关注者 following_count +1，被关注者 followers_count +1
        """
        if data.user_id == data.followed_user_id:
            raise FollowYourselfError(user_id=data.user_id)

        self._get_user_or_raise(data.user_id)
        self._get_user_or_raise(data.followed_user_id)

        result = self._follow_repo.follow(data)

        self._user_repo.update_stats(data.user_id, following_step=1)
        self._user_repo.update_stats(data.followed_user_id, followers_step=1)

        logger.info(
            f"[FOLLOW] user={data.user_id} followed user={data.followed_user_id}"
        )
        return result

    # ==================== D ====================

    def unfollow(self, data: FollowCancel) -> bool:
        """
        取消关注（软删除）。

        流程：
        1. 调用数据层取消关注（可能抛 NotFollowingError）
        2. 关注者 following_count -1，被关注者 followers_count -1
        """
        result = self._follow_repo.unfollow(data)

        self._user_repo.update_stats(data.user_id, following_step=-1)
        self._user_repo.update_stats(data.followed_user_id, followers_step=-1)

        logger.info(
            f"[UNFOLLOW] user={data.user_id} unfollowed user={data.followed_user_id}"
        )
        return result

    def hard_unfollow(self, admin_uid: str, data: FollowCancel) -> bool:
        """
        硬删除关注记录（管理员操作，仅允许对已软删除的关注执行硬删除）。

        流程：
        1. 验证管理员权限
        2. 检查关注关系是否仍有效（deleted_at IS NULL）→ 抛 HardDeleteFollowRequiresSoftDeleteError
        3. 调用数据层硬删除（可能抛 NotFollowingError）
        4. 硬删除后不再更新计数，因为软删除时已经更新过
        """
        self._verify_admin(admin_uid)

        # 如果通过 get_follows 能查到（已过滤软删除），说明未软删除 → 不允许硬删除
        active = self._follow_repo.get_follows(
            FollowDto(user_id=data.user_id, followed_user_id=data.followed_user_id),
            page=0, page_size=1,
        )
        if active.total > 0:
            raise HardDeleteFollowRequiresSoftDeleteError(data.user_id, data.followed_user_id)

        result = self._follow_repo.hard_unfollow(data)

        logger.info(
            f"[HARD_UNFOLLOW] admin={admin_uid} hard-unfollowed "
            f"user={data.user_id} -> user={data.followed_user_id}"
        )
        return result

    # ==================== R ====================

    def get_followings(
        self,
        user_id: str,
        page: int = 0,
        page_size: int = 20,
        to_dict: bool = True,
    ) -> Union[Dict, BatchFollowsOut]:
        """
        获取某用户的关注列表（他关注了谁）。
        """
        result = self._follow_repo.get_follows(
            FollowDto(user_id=user_id), page, page_size,
        )
        return result.model_dump() if to_dict else result

    def get_followers(
        self,
        user_id: str,
        page: int = 0,
        page_size: int = 20,
        to_dict: bool = True,
    ) -> Union[Dict, BatchFollowsOut]:
        """
        获取某用户的粉丝列表（谁关注了他）。
        """
        result = self._follow_repo.get_follows(
            FollowDto(followed_user_id=user_id), page, page_size,
        )
        return result.model_dump() if to_dict else result
