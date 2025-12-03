# domain_exceptions.py
from fastapi import HTTPException, status
from typing import Optional

class UserNotFound(Exception):
    """
    在需要用户存在的场景下未找到对应用户时抛出：
    - 例如 get_user_by_uid / get_user_profile 等
    """

    def __init__(self, user_id: Optional[str] = None, message: Optional[str] = None):
        if message:
            self.message = message
        elif user_id is not None:
            self.message = f"User with id '{user_id}' not found."
        else:
            self.message = "User not found."

        super().__init__(self.message)


class FollowYourselfError(Exception):
    """
    尝试关注自己时抛出：
    - current_uid == target_uid
    """

    def __init__(self, user_id: Optional[str] = None, message: Optional[str] = None):
        if message:
            self.message = message
        elif user_id is not None:
            self.message = f"User '{user_id}' cannot follow themselves."
        else:
            self.message = "You cannot follow yourself."

        super().__init__(self.message)


class AlreadyFollowingError(Exception):
    """
    重复关注同一个用户时抛出：
    - 在业务上你不希望“幂等返回”，而是明确提示已经关注
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        target_id: Optional[str] = None,
        message: Optional[str] = None,
    ):
        if message:
            self.message = message
        elif user_id is not None and target_id is not None:
            self.message = f"User '{user_id}' is already following '{target_id}'."
        else:
            self.message = "Already following this user."

        super().__init__(self.message)


class NotFollowingError(Exception):
    """
    在取消关注时发现当前并未关注目标用户时抛出：
    - 用于区分“正常取消成功”和“本来就没关注”
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        target_id: Optional[str] = None,
        message: Optional[str] = None,
    ):
        if message:
            self.message = message
        elif user_id is not None and target_id is not None:
            self.message = f"User '{user_id}' is not following '{target_id}'."
        else:
            self.message = "Not following this user."

        super().__init__(self.message)

class PasswordMismatchError(Exception):
    """旧密码校验失败"""
    def __init__(self, message="Old password does not match"):
        super().__init__(message)

class PostNotFound(Exception):
    """找不到帖子"""
    def __init__(self, pid: str | None = None, message: str | None = None):
        if message:
            super().__init__(message)
        else:
            super().__init__(f"post {pid} not found")


class InvalidReviewStatusTransition(Exception):
    """帖子审核状态非法流转"""
    def __init__(self, message: str):
        super().__init__(message)

class ForbiddenAction(Exception):
    """帖子发布状态非法流转"""
    def __init__(self, message="Cannot change the publish status of published."):
        super().__init__(message)

class CommentNotFound(Exception):
    """找不到帖子"""
    def __init__(self, cid: str | None = None, message: str | None = None):
        if message:
            super().__init__(message)
        else:
            super().__init__(f"comment {cid} not found")

class CommentNotSoftDeletedError(Exception):
    """只有已软删除的评论才允许被硬删除"""
    def __init__(self, message: str = "comment must be soft-deleted before hard delete"):
        self.message = message
        super().__init__(message)

class AlreadyLikedError(Exception):
    """用户已经对该目标点过赞（未取消），用于阻止重复点赞导致的计数增加"""
    def __init__(self, user_id: str, target_type, target_id: str):
        self.user_id = user_id
        self.target_type = target_type
        self.target_id = target_id
        super().__init__(f"user {user_id} already liked {target_type} {target_id}")


class NotLikedError(Exception):
    """
    取消点赞操作失败：
    - 情况 1：用户从未对该目标点赞
    - 情况 2：用户之前点过赞，但已取消（软删除状态）
    """

    def __init__(self, user_id: str, target_type, target_id: str, message: str = None):
        if message is None:
            message = (
                f"user {user_id} has not liked target_type={target_type}, "
                f"target_id={target_id}"
            )
        self.user_id = user_id
        self.target_type = target_type
        self.target_id = target_id
        super().__init__(message)

class HardDeleteFollowRequiresSoftDeleteError(Exception):
    """
    当管理员尝试硬删除关注记录时：
    - 若该关注关系未处于软删除状态（deleted_at is NULL）
    - 则必须先软删除才能进入硬删除

    用于业务层阻止不正确的删除流程
    """

    def __init__(self, user_id: str, followed_user_id: str):
        self.user_id = user_id
        self.followed_user_id = followed_user_id
        super().__init__(
            f"follow relation {user_id} -> {followed_user_id} must be soft-deleted before hard delete"
        )
