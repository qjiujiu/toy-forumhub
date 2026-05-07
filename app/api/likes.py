# app/api/v1/likes.py  或类似路径

from fastapi import APIRouter, Depends

from app.schemas.like import (
    LikeCreate,
    LikeCancel,
    LikeOut,
    LikeAdminOut,
    BatchLikesOut,
    BatchLikesAdminOut,
    GetTargetLike,
)
from app.models.like import LikeTargetType

from app.core.biz_response import BizResponse
from app.core.logx import logger

from app.service import like_svc

from app.storage.database import (
    get_user_repo,
    get_post_repo,
    get_comment_repo,
    get_like_repo,
    get_poststats_repo,
)
from app.storage.user.user_interface import IUserRepository
from app.storage.post.post_interface import IPostRepository
from app.storage.comment.comment_interface import ICommentRepository
from app.storage.like.like_interface import ILikeRepository
from app.storage.post_stats.post_stats_interface import IPostStatsRepository

from app.core.exceptions import (
    UserNotFound,
    PostNotFound,
    CommentNotFound,
    AlreadyLikedError,
    NotLikedError,
)
from fastapi.encoders import jsonable_encoder

likes_router = APIRouter(prefix="/likes", tags=["likes"])


# -------------------------- 点赞 -------------------------- #

@likes_router.post("/", response_model=LikeOut)
def like_target(
    data: LikeCreate,
    user_repo: IUserRepository = Depends(get_user_repo),
    post_repo: IPostRepository = Depends(get_post_repo),
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    post_stats_repo: IPostStatsRepository = Depends(get_poststats_repo),
    like_repo: ILikeRepository = Depends(get_like_repo),
):
    """
    点赞目标（帖子/评论）：

    - 校验用户是否存在
    - 校验帖子 / 评论是否存在
    - 调用 like_svc.like_target 完成点赞 + 更新计数
    """
    try:
        like = like_svc.like_target(
            user_repo=user_repo,
            post_repo=post_repo,
            comment_repo=comment_repo,
            post_stats_repo=post_stats_repo,
            like_repo=like_repo,
            data=data,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(like))
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except AlreadyLikedError as e:
        # 重复点赞：客户端逻辑错误，一般用 409 / 400
        logger.info(f"AlreadyLikedError: {e}")
        return BizResponse(data=None, msg=str(e), status_code=409)
    except Exception as e:
        logger.exception("like_target error")
        return BizResponse(data=None, msg=str(e), status_code=500)


# -------------------------- 取消点赞 -------------------------- #

@likes_router.post("/cancel", response_model=bool)
def cancel_like(
    data: LikeCancel,
    user_repo: IUserRepository = Depends(get_user_repo),
    post_stats_repo: IPostStatsRepository = Depends(get_poststats_repo),
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    like_repo: ILikeRepository = Depends(get_like_repo),
):
    """
    取消点赞（软删除）：

    - 校验用户是否存在
    - 调用 like_svc.cancel_like 完成取消 + 更新计数
    """
    try:
        ok = like_svc.cancel_like(
            user_repo=user_repo,
            post_stats_repo=post_stats_repo,
            comment_repo=comment_repo,
            like_repo=like_repo,
            data=data,
        )
        return BizResponse(data=jsonable_encoder(ok))
    except UserNotFound as e:
        return BizResponse(data=False, msg=str(e), status_code=404)
    except NotLikedError as e:
        # 没有点赞就取消，属于客户端错误
        logger.info(f"NotLikedError: {e}")
        return BizResponse(data=False, msg=str(e), status_code=409)
    except Exception as e:
        logger.exception("cancel_like error")
        return BizResponse(data=False, msg=str(e), status_code=500)


# -------------------------- 查询：按目标 -------------------------- #

@likes_router.get("/by-target", response_model=BatchLikesOut)
def list_likes_by_target(
    data: GetTargetLike,
    page: int = 0,
    page_size: int = 10,
    like_repo: ILikeRepository = Depends(get_like_repo),
):
    """
    查询某个目标（帖子 / 评论）的所有 **有效** 点赞记录（分页）
    - 不包含软删除
    """
    try:
        result = like_svc.list_likes_by_target(
            like_repo=like_repo,
            data=data,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("list_likes_by_target error")
        return BizResponse(data={"total": 0, "count": 0, "items": []}, msg=str(e), status_code=500)


# -------------------------- 查询：按用户 -------------------------- #

@likes_router.get("/by-user/{user_id}", response_model=BatchLikesOut)
def list_likes_by_user(
    user_id: str,
    page: int = 0,
    page_size: int = 10,
    like_repo: ILikeRepository = Depends(get_like_repo),
):
    """
    查询某个用户的所有 **有效** 点赞记录（分页）
    - 包含该用户对帖子和评论的点赞
    """
    try:
        result = like_svc.list_likes_by_user(
            like_repo=like_repo,
            user_id=user_id,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("list_likes_by_user error")
        return BizResponse(data={"total": 0, "count": 0, "items": []}, msg=str(e), status_code=500)


# -------------------------- 管理员：按目标 -------------------------- #

@likes_router.get("/admin/by-target", response_model=BatchLikesAdminOut)
def admin_list_likes_by_target(
    data: GetTargetLike,
    page: int = 0,
    page_size: int = 10,
    like_repo: ILikeRepository = Depends(get_like_repo),
):
    """
    管理员：查询某个目标的所有点赞记录（包含软删除）
    """
    try:
        result = like_svc.admin_list_likes_by_target(
            like_repo=like_repo,
            data=data,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("admin_list_likes_by_target error")
        return BizResponse(data={"total": 0, "count": 0, "items": []}, msg=str(e), status_code=500)


# -------------------------- 管理员：按用户 -------------------------- #

@likes_router.get("/admin/by-user/{user_id}", response_model=BatchLikesAdminOut)
def admin_list_likes_by_user(
    user_id: str,
    page: int = 0,
    page_size: int = 10,
    like_repo: ILikeRepository = Depends(get_like_repo),
):
    """
    管理员：查询某个用户的所有点赞记录（包含软删除）
    """
    try:
        result = like_svc.admin_list_likes_by_user(
            like_repo=like_repo,
            user_id=user_id,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("admin_list_likes_by_user error")
        return BizResponse(data={"total": 0, "count": 0, "items": []}, msg=str(e), status_code=500)
