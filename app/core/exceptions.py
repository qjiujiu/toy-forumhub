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