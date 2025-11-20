from fastapi import APIRouter, Depends
from app.schemas.follow import BatchFollowsOut, FollowCreate, FollowCancel

from app.core.biz_response import BizResponse
from app.service import follow_svc

from app.storage.database import (
    get_user_repo,
    get_usersta_repo,
    get_follow_repo,
)
from app.storage.user_stats.user_stats_interface import IUserStatsRepository
from app.storage.follow.follow_interface import IFollowRepository
from app.storage.user.user_interface import IUserRepository
from app.core.exceptions import (
    UserNotFound,
    FollowYourselfError,
    AlreadyFollowingError,
    NotFollowingError,
)
from app.core.logx import logger
logger.is_debug(True)

follows_router = APIRouter(prefix="/follows", tags=["follows"])


@follows_router.post("/", response_model=None)
def follow_user(follow: FollowCreate, follow_repo: IFollowRepository = Depends(get_follow_repo), stats_repo: IUserStatsRepository = Depends(get_usersta_repo), user_repo: IUserRepository = Depends(get_user_repo),):
    """
    关注用户：
    - current_uid 关注 target_uid
    - 更新双方的关注数/粉丝数
    """
    try:
        follow = follow_svc.follow_user(
            follow_repo=follow_repo,
            stats_repo=stats_repo,
            user_repo=user_repo,
            follow=follow,
            to_dict=True,
        )
        return BizResponse(data=follow)
    except FollowYourselfError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except AlreadyFollowingError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@follows_router.delete("/")
def cancel_follow(cancel_follow: FollowCancel, follow_repo: IFollowRepository = Depends(get_follow_repo), stats_repo: IUserStatsRepository = Depends(get_usersta_repo),):
    """
    取消关注：
    - current_uid 取消关注 target_uid
    - 更新双方的关注数/粉丝数
    """
    try:
        ok = follow_svc.cancel_follow(
            follow_repo=follow_repo,
            stats_repo=stats_repo,
            cancel_follow=cancel_follow
        )
        if not ok:
            return BizResponse(data=False, msg="cancel following failed", status_code=400)
        return BizResponse(data=True)
    except NotFollowingError as e:
        return BizResponse(data=False, msg=str(e), status_code=400)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)


@follows_router.get("/following/{uid}", response_model=BatchFollowsOut)
def list_following(uid: str, page: int = 0, page_size: int = 10, follow_repo: IFollowRepository = Depends(get_follow_repo),):
    """
    我关注的人列表
    """
    logger.debug("ok")
    try:
        result = follow_svc.list_following(
            follow_repo=follow_repo,
            current_uid=uid,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@follows_router.get("/followers/{uid}", response_model=BatchFollowsOut)
def list_followers(uid: str, page: int = 0, page_size: int = 10, follow_repo: IFollowRepository = Depends(get_follow_repo),):
    """
    我的粉丝列表
    """
    logger.debug("ok")
    try:
        result = follow_svc.list_followers(
            follow_repo=follow_repo,
            current_uid=uid,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)
