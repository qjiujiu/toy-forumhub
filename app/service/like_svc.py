from typing import Dict

from app.schemas.like import (
    LikeCreate,
    LikeCancel,
    LikeOut,
    BatchLikesOut,
    LikeAdminOut,
    BatchLikesAdminOut,
    GetTargetLike,
)
from app.models.like import LikeTargetType

from app.storage.like.like_interface import ILikeRepository
from app.storage.user.user_interface import IUserRepository
from app.storage.post.post_interface import IPostRepository
from app.storage.post_stats.post_stats_interface import IPostStatsRepository
from app.storage.comment.comment_interface import ICommentRepository

from app.core.exceptions import (
    UserNotFound,
    PostNotFound,
    CommentNotFound,
)
from app.core.logx import logger


# ----------------------------- 点赞 / 取消点赞 -----------------------------
def like_target(
    user_repo: IUserRepository,
    post_repo: IPostRepository,
    comment_repo: ICommentRepository,
    post_stats_repo: IPostStatsRepository,
    like_repo: ILikeRepository,
    data: LikeCreate,
    to_dict: bool = True,
) -> Dict | LikeOut:
    """
    点赞目标（帖子 / 评论）：

    1. 校验用户是否存在
    2. 校验目标是否存在（帖子或评论）
    3. 调用 like_repo.like() 创建 / 恢复点赞
       - 如果抛 AlreadyLikedError：说明本来就已经点赞了，业务上视为“错误”，交给接口层返回 400/409
    4. 根据 target_type 更新对应的 like_count（只在真正“新增/恢复”点赞时）
    5. 返回 LikeOut
    """

    # 1. 校验用户是否存在
    user = user_repo.get_user_by_uid(data.user_id)
    if not user:
        raise UserNotFound(message=f"user {data.user_id} not found")

    # 2. 校验点赞目标是否存在
    if data.target_type == LikeTargetType.POST:
        post = post_repo.viewer_get_post_by_pid(data.target_id)
        if not post:
            raise PostNotFound(message=f"post {data.target_id} not found")
    elif data.target_type == LikeTargetType.COMMENT:
        comment = comment_repo.get_comment_by_cid_for_user(data.target_id)
        if not comment:
            raise CommentNotFound(message=f"comment {data.target_id} not found")
    else:
        raise ValueError(f"unsupported target_type: {data.target_type}")

    # 3. 点赞（这里如果是重复点赞，会在 repo 内抛 AlreadyLikedError）
    like_out: LikeOut = like_repo.like(data)

    # 4. 只有 “确实新建 / 恢复” 成功才会走到这里 → 安全地 +1
    if data.target_type == LikeTargetType.POST:
        post_stats_repo.update_likes(post_id=data.target_id, step=1)
    else:
        comment_repo.update_like_count(cid=data.target_id, step=1)

    logger.info(
        f"User {data.user_id} liked target_type={data.target_type} "
        f"target_id={data.target_id}, lid={like_out.lid}"
    )

    return like_out.model_dump() if to_dict else like_out


def cancel_like(
    user_repo: IUserRepository,
    post_stats_repo: IPostStatsRepository,
    comment_repo: ICommentRepository,
    like_repo: ILikeRepository,
    data: LikeCancel,
    to_dict: bool = True,
) -> Dict | LikeOut:
    """
    取消点赞（软删除）：

    1. 校验用户是否存在
    2. 调用 like_repo.cancel_like()：
       - 成功返回 LikeOut：本次从“已点赞” -> “未点赞”，需要把 like_count -1
       - 抛 NotLikedError：当前本来就“未点赞”，由接口层转换为 409/400
    """

    # 1. 校验用户是否存在
    user = user_repo.get_user_by_uid(data.user_id)
    if not user:
        raise UserNotFound(message=f"user {data.user_id} not found")

    # 2. 取消点赞（可能抛 NotLikedError）
    like_out = like_repo.cancel_like(data)

    # 3. 只有真正取消成功时才会执行到这里，安全地 -1
    if data.target_type == LikeTargetType.POST:
        post_stats_repo.update_likes(post_id=data.target_id, step=-1)
    else:
        comment_repo.update_like_count(cid=data.target_id, step=-1)

    logger.info(
        f"User {data.user_id} cancel like target_type={data.target_type}, "
        f"target_id={data.target_id}"
    )
    return like_out.model_dump() if to_dict else like_out


# ----------------------------- 查询：普通视角 -----------------------------


def list_likes_by_target(
    like_repo: ILikeRepository,
    data: GetTargetLike,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchLikesOut:
    """
    查询某个目标（帖子 / 评论）的有效点赞列表（分页）：
    - 只返回未软删除的点赞记录
    """

    result = like_repo.list_likes_by_target(
        target_type=data.target_type,
        target_id=data.target_id,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result


def list_likes_by_user(
    like_repo: ILikeRepository,
    user_id: str,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchLikesOut:
    """
    查询某个用户的有效点赞记录（分页）：
    - 包含该用户对帖子和评论的所有点赞
    """
    result = like_repo.list_likes_by_user(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result


# ----------------------------- 查询：管理员视角 -----------------------------


def admin_list_likes_by_target(
    like_repo: ILikeRepository,
    data: GetTargetLike,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchLikesAdminOut:
    """
    管理员：查询某个目标（帖子 / 评论）的所有点赞记录（含软删）
    """
    result = like_repo.admin_list_likes_by_target(
        target_type=data.target_type,
        target_id=data.target_id,
        page=page,
        page_size=page_size,
    )

    return result.model_dump() if to_dict else result


def admin_list_likes_by_user(
    like_repo: ILikeRepository,
    user_id: str,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchLikesAdminOut:
    """
    管理员：查询某个用户的所有点赞记录（含软删）
    """
    result = like_repo.admin_list_likes_by_user(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )

    return result.model_dump() if to_dict else result
