from typing import Optional, Dict, List

from app.schemas.follow import (
    FollowCreate,
    FollowOut,
    FollowCancel,
    BatchFollowsOut,
)
from app.storage.user.user_interface import IUserRepository
from app.storage.user_stats.user_stats_interface import IUserStatsRepository
from app.storage.follow.follow_interface import IFollowRepository

from app.core.logx import logger
from app.core.exceptions import (
    UserNotFound,
    FollowYourselfError,
    AlreadyFollowingError,
    NotFollowingError,
    HardDeleteFollowRequiresSoftDeleteError,
)
logger.is_debug(True)

def follow_user(follow_repo: IFollowRepository, stats_repo: IUserStatsRepository, user_repo: IUserRepository, follow: FollowCreate, to_dict: bool = True,) -> Dict | FollowOut:
    """
    关注用户：
    1. 检查关注用户是否存在
    2. 检查是否自己关注自己（禁止）
    3. 检查是否已关注，如果已关注可直接返回或抛错（这里选择直接返回）
    4. 创建 Follow 记录
    5. 更新统计：current_uid.following +1, target_uid.followers +1

    实际上步骤1,2,3在前端都会约束，或许后端不需要检查，比如被关注用户不存在就无法找到关注按钮，关注用户自身首页不会出现关注按钮，已关注的用户关注按钮是取关按钮
    """
    current_uid = follow.user_id
    target_uid = follow.followed_user_id

    current_user = user_repo.get_user_by_uid(uid=current_uid)
    if not current_user:
        raise UserNotFound(message=f"current_user {current_uid} not found")
    target_user = user_repo.get_user_by_uid(uid=target_uid)
    if not target_user:
        raise UserNotFound(message=f"target_user {target_uid} not found")

    if current_uid == target_uid:
        raise FollowYourselfError("cannot follow yourself")

    # 如果已经关注，直接返回当前关注关系（不再重复计数）
    if follow_repo.is_following(current_uid, target_uid):
        raise AlreadyFollowingError(current_uid, target_uid)

    # 1. 创建关注记录
    follow = follow_repo.create_follow(
        FollowCreate(user_id=current_uid, followed_user_id=target_uid)
    )

    # 2. 更新统计：当前用户关注数 +1，对方粉丝数 +1
    stats_repo.update_following(current_uid, step=1)
    stats_repo.update_followers(target_uid, step=1)

    return follow.model_dump() if to_dict else follow


def cancel_follow(follow_repo: IFollowRepository, stats_repo: IUserStatsRepository, cancel_follow: FollowCancel) -> bool:
    """
    取消关注：
    1. 检查是否正在关注
    2. 软删除 Follow 记录
    3. 更新统计：current_uid.following -1, target_uid.followers -1
    """
    current_uid = cancel_follow.user_id
    target_uid = cancel_follow.followed_user_id

    if not follow_repo.is_following(current_uid, target_uid):
        raise NotFollowingError(current_uid, target_uid)

    ok = follow_repo.cancel_follow(data=cancel_follow)
    if not ok:
        return False

    # 更新统计（防止减到负数，由数据层保证）
    stats_repo.update_following(current_uid, step=-1)
    stats_repo.update_followers(target_uid, step=-1)

    return True

def hard_delete_follow(
    follow_repo: IFollowRepository,
    user_repo: IUserRepository,
    data: FollowCancel,
) -> bool:
    """
    管理员硬删除关注关系（需要先软删除）：

    1. 校验双方用户存在
    2. admin_get_follow 查询关注记录（包含 deleted_at）
    3. 如果不存在 → 可以认为不存在这条关系（看你要不要抛 NotFollowingError）
    4. 如果 deleted_at is None → 说明未软删，不允许硬删，抛 HardDeleteFollowRequiresSoftDeleteError
    5. 如果 deleted_at 不为 None → 允许硬删，调用 follow_repo.hard_delete_follow(...)
       注意：不再修改统计 following / followers
    """

    # 1. 用户存在性校验（可选，但推荐）
    follower = user_repo.admin_get_user_by_uid(data.user_id)
    if not follower:
        raise UserNotFound(message=f"user {data.user_id} not found")

    followed = user_repo.admin_get_user_by_uid(data.followed_user_id)
    if not followed:
        raise UserNotFound(message=f"user {data.followed_user_id} not found")

    # 2. 管理员视角查关注记录
    follow = follow_repo.admin_get_follow(
        user_id=data.user_id,
        followed_user_id=data.followed_user_id,
    )

    if not follow:
        # 这里你也可以选择抛 NotFollowingError
        logger.warning(
            f"[ADMIN] hard delete follow failed: "
            f"{data.user_id} -> {data.followed_user_id} not found"
        )
        return False

    # 3. 必须已经软删除才允许硬删
    if follow.deleted_at is None:
        # 说明当前还是“正常关注”状态，业务不允许直接硬删
        raise HardDeleteFollowRequiresSoftDeleteError(
            user_id=data.user_id,
            followed_user_id=data.followed_user_id,
        )

    # 4. deleted_at 不为 None → 可以执行硬删除（不改统计）
    ok = follow_repo.hard_delete_follow(
        user_id=data.user_id,
        followed_user_id=data.followed_user_id,
    )

    if ok:
        logger.info(
            f"[ADMIN] hard deleted follow relation: "
            f"{data.user_id} -> {data.followed_user_id}"
        )
    else:
        logger.warning(
            f"[ADMIN] hard delete follow failed at repo: "
            f"{data.user_id} -> {data.followed_user_id}"
        )

    return ok

def list_following(follow_repo: IFollowRepository, current_uid: str, page: int = 0, page_size: int = 10, to_dict: bool = True) -> Dict | BatchFollowsOut:
    """
    我关注的人列表
    - 返回 FollowUserOut 列表（对方 UserOut + is_mutual）
    """
    result = follow_repo.list_following(
        user_id=current_uid,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result


def list_followers(follow_repo: IFollowRepository, current_uid: str, page: int = 0, page_size: int = 10, to_dict: bool = True) -> Dict | BatchFollowsOut:
    """
    我的粉丝列表
    - 返回 FollowUserOut 列表（对方 UserOut + is_mutual）
    """
    logger.debug("ok")
    result = follow_repo.list_followers(
        user_id=current_uid,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result