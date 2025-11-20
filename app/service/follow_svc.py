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

    target_user = user_repo.get_user_by_uid(uid=target_uid)
    if not target_user:
        raise UserNotFound(f"target_user {target_uid} not found")

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