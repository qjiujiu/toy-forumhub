from typing import Optional, Dict, List

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    AdminUserUpdate,
    UserOut,
    UserDetailOut,
    BatchUsersOut,
    UserPasswordUpdate,
    BatchUsersAllOut,
    UserAllOut
)
from app.schemas.user_stats import (
    UserStatsOut,
    UserStatsWithUserOut,
)
from app.storage.user.user_interface import IUserRepository
from app.storage.user_stats.user_stats_interface import IUserStatsRepository
from app.storage.follow.follow_interface import IFollowRepository

from app.core.logx import logger
from app.core.exceptions import UserNotFound, PasswordMismatchError

from app.core.security import hash_password, verify_password


def create_user(user_repo: IUserRepository, stats_repo: IUserStatsRepository, user_data: UserCreate, to_dict: bool = True) -> Dict | UserOut:
    """
    创建用户：
    1. 对明文密码做 Argon2 哈希
    2. 创建 User 记录（password 存储哈希）
    3. 初始化 UserStats 记录（following_count = 0, followers_count = 0）
    """

    # 1. 对密码进行哈希（如果允许第三方登录密码为空，要注意判断）
    if user_data.password:
        hashed = hash_password(user_data.password)
        user_data.password = hashed

    # 2. 创建用户记录
    new_user = user_repo.create_user(user_data)
    logger.info(f"Created user uid={new_user.uid}")

    # 3. 为用户创建统计记录
    stats_repo.create_for_user(new_user.uid)
    logger.info(f"Initialized statistics for user uid={new_user.uid}")

    return new_user.model_dump() if to_dict else new_user

def get_batch_users(user_repo: IUserRepository, page: int = 0, page_size: int = 10, to_dict: bool = True) -> Dict | BatchUsersOut:
    """
    分页获取用户列表（不含统计信息）
    """
    result = user_repo.get_batch_users(page=page, page_size=page_size)
    return result.model_dump() if to_dict else result


def get_users_by_username(user_repo: IUserRepository, username: str, page: int = 0, page_size: int = 10, to_dict: bool = True) -> Dict | BatchUsersOut:
    """
    根据用户名分页查询同名用户
    """
    result = user_repo.get_users_by_username(
        username=username,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result


def get_user_by_uid(user_repo: IUserRepository, uid: str, to_dict: bool = True) -> Optional[Dict | UserOut]:
    """
    根据 uid 获取用户基础信息
    """
    user = user_repo.get_user_by_uid(uid)
    if not user:
        raise UserNotFound(f"user {uid} not found")
    return UserOut.model_validate(user).model_dump() if to_dict else user


def get_user_profile(stats_repo: IUserStatsRepository, uid: str, to_dict: bool = True) -> Optional[Dict | UserStatsWithUserOut]:
    """
    用户详情：User 信息 + 关注数/粉丝数
    这里直接用 UserStatsWithUserOut（由 stats_repo join user 拼出）
    """
    profile = stats_repo.get_with_user_by_user_id(uid)
    if not profile:
        return UserNotFound(f"user {uid} not found")
    return profile.model_dump() if to_dict else profile


def update_user(user_repo: IUserRepository, uid: str, data: UserUpdate, to_dict: bool = True) -> Optional[Dict | UserOut]:
    """
    普通用户更新自己的信息
    """
    updated = user_repo.update_user(uid, data)
    if not updated:
        return None
    return updated.model_dump() if to_dict else updated


def admin_update_user(user_repo: IUserRepository, uid: str, data: AdminUserUpdate, to_dict: bool = True) -> Optional[Dict | UserOut]:
    """
    管理员更新用户信息（包含角色/状态）
    """
    updated = user_repo.admin_update_user(uid, data)
    if not updated:
        return None
    return updated.model_dump() if to_dict else updated


def change_password(user_repo: IUserRepository, uid: str, data: UserPasswordUpdate) -> bool:
    """
    修改密码：
    - 业务层负责校验 old_password 是否正确（需要结合登录表/认证逻辑）
    - 这里仅负责调用仓库层 update_password
    """
    # TODO: 先在业务层校验 old_password 是否正确（略）
    user = user_repo.get_user_by_uid(uid)
    if not user:
        raise UserNotFound(f"user {uid} not found")
    if not verify_password(data.old_password, user.password):
        raise PasswordMismatchError()

    # 对密码进行哈希
    if data.new_password:
        hashed = hash_password(data.new_password)
        data.new_password = hashed

    return user_repo.update_password(uid, hashed)


def soft_delete_user(user_repo: IUserRepository, uid: str) -> bool:
    """
    软删除用户（只标记 deleted_at）
    - 关联的 Follow / UserStats 可视业务决定是否保留或单独清理
    """
    ok = user_repo.soft_delete_user(uid)
    if ok:
        logger.info(f"Soft deleted user uid={uid}")
    return ok


# ------------------------------------ 管理员用 ----------------------------------------
def hard_delete_user(user_repo: IUserRepository, uid: str) -> bool:
    """
    通常只有管理员才能调用。

    硬删除用户，在数据表中以及设置用户的相关记录一并删除其中包含：
    1. 删除与该用户相关的所有关注记录
    2. 删除用户的统计记录
    3. 删除用户的基本信息记录
    4. 删除用户帖子记录
    5. 删除用户的点赞记录
    6. 删除用户的评论记录

    TODO 删除用户的点赞，评论以及关注记录的时候，涉及count字段的变化，所以在删除之前需要先更新相关的count字段
    """
    # # 1. 删关注关系
    # deleted_follows = follow_repo.hard_delete_all_by_user(uid)
    # logger.info(f"Hard deleted {deleted_follows} follow records for user uid={uid}")

    # # 2. 删统计记录
    # stats_repo.delete_by_user_id(uid)
    # logger.info(f"Hard deleted statistics for user uid={uid}")

    # 3. 删用户
    ok = user_repo.hard_delete_user(uid)
    if ok:
        logger.info(f"Hard deleted user uid={uid}")
    return ok

def admin_get_users(
    user_repo: IUserRepository,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchUsersAllOut:
    """
    管理员：分页查看所有用户（包含软删）
    """
    result = user_repo.admin_get_users(
        page=page,
        page_size=page_size,
    )

    logger.info(
        f"[ADMIN] list all users page={page}, page_size={page_size}, count={result.count}"
    )

    return result.model_dump() if to_dict else result

def admin_get_user_by_uid(
    user_repo: IUserRepository,
    uid: str,
    to_dict: bool = True,
) -> Dict | UserAllOut:
    """
    管理员根据 uid 获取用户详情：
    - 不过滤软删除（数据层已实现 admin_get_user_by_uid）
    - 响应体为 UserAllOut（包含更多字段）
    """
    user = user_repo.admin_get_user_by_uid(uid)
    if not user:
        raise UserNotFound(f"user {uid} not found")

    logger.info(f"[ADMIN] get user uid={uid}")
    return user.model_dump() if to_dict else user

def admin_get_users_by_username(
    user_repo: IUserRepository,
    username: str,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchUsersAllOut:
    """
    管理员根据用户名分页查询用户：
    - 不过滤软删除
    - 返回 BatchUsersAllOut
    """
    result = user_repo.admin_get_users_by_username(
        username=username,
        page=page,
        page_size=page_size,
    )

    logger.info(
        f"[ADMIN] get users by username='{username}', "
        f"page={page}, page_size={page_size}, count={result.count}"
    )

    return result.model_dump() if to_dict else result

def admin_list_deleted_users(
    user_repo: IUserRepository,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchUsersAllOut:
    """
    管理员查看所有软删除用户：
    - 只查 deleted_at IS NOT NULL
    - 返回 BatchUsersAllOut
    """
    result = user_repo.admin_list_deleted_users(
        page=page,
        page_size=page_size,
    )

    logger.info(
        f"[ADMIN] list deleted users page={page}, "
        f"page_size={page_size}, count={result.count}"
    )

    return result.model_dump() if to_dict else result

def admin_list_abnormal_status_users(
    user_repo: IUserRepository,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchUsersAllOut:
    """
    管理员查看异常状态用户：
    - “异常状态”的定义由数据层决定（例如 status = 1/2）
    - 返回 BatchUsersAllOut
    """
    result = user_repo.admin_list_abnormal_status_users(
        page=page,
        page_size=page_size,
    )

    logger.info(
        f"[ADMIN] list abnormal status users page={page}, "
        f"page_size={page_size}, count={result.count}"
    )

    return result.model_dump() if to_dict else result
