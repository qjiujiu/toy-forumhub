from fastapi import APIRouter, Depends

from app.schemas.v2.like import (
    LikeCreate,
    LikeCancel,
    GetUserLike,
    GetTargetLike,
    LikeOut,
    BatchLikesOut,
)
from app.service.v2.like_svc import LikeService

from app.storage.v2.database import (
    get_like_repo,
    get_post_repo,
    get_comment_repo,
)
from app.storage.v2.like.like_interface import ILikeRepository
from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.comment.comment_interface import ICommentRepository

from app.core.exceptions import AlreadyLikedError, NotLikedError
from app.core.logx import logger
from app.core.biz_response import BizResponse


def get_like_service(
    like_repo: ILikeRepository = Depends(get_like_repo),
    post_repo: IPostRepository = Depends(get_post_repo),
    comment_repo: ICommentRepository = Depends(get_comment_repo),
) -> LikeService:
    return LikeService(like_repo, post_repo, comment_repo)


likes_router = APIRouter(prefix="/likes", tags=["likes"])


@likes_router.post("/", response_model=LikeOut)
def like(
    data: LikeCreate,
    like_service: LikeService = Depends(get_like_service),
):
    """
    点赞（帖子或评论）。

    - target_type=0 为帖子点赞，target_type=1 为评论点赞
    - 同一用户对同一目标只能有一条有效点赞
    """
    try:
        result = like_service.like(data)
        return BizResponse(data=result)
    except (AlreadyLikedError, ValueError) as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@likes_router.delete("/")
def cancel_like(
    data: LikeCancel,
    like_service: LikeService = Depends(get_like_service),
):
    """
    取消点赞（软删除）。

    - 同一用户对同一目标只能取消已存在的有效点赞
    - 已取消的记录不可重复取消
    """
    try:
        ok = like_service.cancel_like(data)
        return BizResponse(data=ok)
    except NotLikedError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=False, msg=str(e), status_code=500)


@likes_router.get("/user", response_model=BatchLikesOut)
def get_user_likes(
    user_id: str,
    target_type: int,
    page: int = 0,
    page_size: int = 20,
    like_service: LikeService = Depends(get_like_service),
):
    """
    获取某用户在某类型下的点赞列表。
    - 例如：用户 A 点赞过的所有帖子
    """
    try:
        query = GetUserLike(user_id=user_id, target_type=target_type)
        result = like_service.get_user_likes(
            query=query, page=page, page_size=page_size, to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@likes_router.get("/target", response_model=BatchLikesOut)
def get_target_likes(
    target_type: int,
    target_id: str,
    page: int = 0,
    page_size: int = 20,
    like_service: LikeService = Depends(get_like_service),
):
    """
    获取某内容（帖子/评论）下的所有点赞用户列表。
    - 例如：帖子 P1 被哪些用户点赞过
    """
    try:
        query = GetTargetLike(target_type=target_type, target_id=target_id)
        result = like_service.get_target_likes(
            query=query, page=page, page_size=page_size, to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)
