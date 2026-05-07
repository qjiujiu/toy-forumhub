from fastapi import APIRouter, Depends

from app.schemas.v2.follow import (
    FollowCreate,
    FollowCancel,
    FollowOut,
    BatchFollowsOut,
)
from app.service.v2.follow_svc import FollowService

from app.storage.v2.database import (
    get_follow_repo,
    get_user_repo,
)
from app.storage.v2.follow.follow_interface import IFollowRepository
from app.storage.v2.user.user_interface import IUserRepository

from app.core.exceptions import (
    AlreadyFollowingError,
    FollowYourselfError,
    NotFollowingError,
    UserNotFound,
    AdminPermissionDenied,
)
from app.core.logx import logger
from app.core.biz_response import BizResponse


def get_follow_service(
    follow_repo: IFollowRepository = Depends(get_follow_repo),
    user_repo: IUserRepository = Depends(get_user_repo),
) -> FollowService:
    return FollowService(follow_repo, user_repo)


follows_router = APIRouter(prefix="/follows", tags=["follows"])


@follows_router.post("/")
def follow(
    data: FollowCreate,
    follow_service: FollowService = Depends(get_follow_service),
):
    """
    关注用户。

    - 不能关注自己
    - 不能重复关注同一用户
    """
    try:
        ok = follow_service.follow(data)
        return BizResponse(data=ok)
    except FollowYourselfError as e:
        return BizResponse(data=False, msg=str(e), status_code=400)
    except UserNotFound as e:
        return BizResponse(data=False, msg=str(e), status_code=404)
    except AlreadyFollowingError as e:
        return BizResponse(data=False, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=False, msg=str(e), status_code=500)


@follows_router.delete("/")
def unfollow(
    data: FollowCancel,
    follow_service: FollowService = Depends(get_follow_service),
):
    """
    取消关注（软删除）。
    """
    try:
        ok = follow_service.unfollow(data)
        return BizResponse(data=ok)
    except NotFollowingError as e:
        return BizResponse(data=False, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=False, msg=str(e), status_code=500)


@follows_router.delete("/hard")
def hard_unfollow(
    admin_uid: str,
    data: FollowCancel,
    follow_service: FollowService = Depends(get_follow_service),
):
    """
    硬删除关注记录（管理员操作）。
    """
    try:
        ok = follow_service.hard_unfollow(admin_uid, data)
        return BizResponse(data=ok)
    except AdminPermissionDenied as e:
        return BizResponse(data=False, msg=str(e), status_code=403)
    except UserNotFound as e:
        return BizResponse(data=False, msg=str(e), status_code=404)
    except NotFollowingError as e:
        return BizResponse(data=False, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=False, msg=str(e), status_code=500)


@follows_router.get("/followings/{user_id}", response_model=BatchFollowsOut)
def get_followings(
    user_id: str,
    page: int = 0,
    page_size: int = 20,
    follow_service: FollowService = Depends(get_follow_service),
):
    """
    获取某用户的关注列表（他关注了谁）。
    """
    try:
        result = follow_service.get_followings(
            user_id=user_id, page=page, page_size=page_size, to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@follows_router.get("/followers/{user_id}", response_model=BatchFollowsOut)
def get_followers(
    user_id: str,
    page: int = 0,
    page_size: int = 20,
    follow_service: FollowService = Depends(get_follow_service),
):
    """
    获取某用户的粉丝列表（谁关注了他）。
    """
    try:
        result = follow_service.get_followers(
            user_id=user_id, page=page, page_size=page_size, to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)
