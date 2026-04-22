from fastapi import APIRouter, Depends

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    AdminUserUpdate,
    UserOut,
    BatchUsersOut,
    UserPasswordUpdate,
    BatchUsersAllOut,
    UserAllOut
)
from app.schemas.user_stats import UserStatsWithUserOut
from app.schemas.follow import BatchFollowsOut

from app.core.biz_response import BizResponse
from app.service_refactor.user_svc import UserService

from app.storage.database import (
    get_user_repo,
    get_usersta_repo,
    get_follow_repo,
)
from app.storage.user.user_interface import IUserRepository
from app.storage.user_stats.user_stats_interface import IUserStatsRepository
from app.storage.follow.follow_interface import IFollowRepository

from app.core.exceptions import (
    UserNotFound,
    PasswordMismatchError,
    FollowYourselfError,
    AlreadyFollowingError,
    NotFollowingError,
)
from app.core.logx import logger
from fastapi.encoders import jsonable_encoder


def get_user_service(
    user_repo: IUserRepository = Depends(get_user_repo),
    stats_repo: IUserStatsRepository = Depends(get_usersta_repo),
    follow_repo: IFollowRepository = Depends(get_follow_repo),
) -> UserService:
    return UserService(user_repo, stats_repo, follow_repo)


def get_user_service_basic(
    user_repo: IUserRepository = Depends(get_user_repo),
    stats_repo: IUserStatsRepository = Depends(get_usersta_repo),
) -> UserService:
    return UserService(user_repo, stats_repo)


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("/", response_model=UserOut)
def create_user(
    user: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """
    创建用户：
    - 创建 user 表记录
    - 初始化 user_statistics（关注数/粉丝数为 0）
    """
    try:
        new_user = user_service.create_user(
            user_data=user,
            to_dict=True,
        )
        return BizResponse(data=new_user)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)
    

@users_router.get("/", response_model=BatchUsersOut)
def query_batch_users(
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    分页获取用户列表（只含基础信息）
    """
    try:
        result = user_service.get_batch_users(
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@users_router.get("/username/{username}", response_model=BatchUsersOut)
def get_users_by_username(
    username: str,
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    根据用户名分页查询同名用户
    """
    try:
        result = user_service.get_users_by_username(
            username=username,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@users_router.get("/id/{uid}", response_model=UserOut)
def query_user_basic(
    uid: str,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    根据 uid 查询用户基础信息（不含关注/粉丝统计）
    """
    try:
        user = user_service.get_user_by_uid(
            uid=uid,
            to_dict=True,
        )
        return BizResponse(data=user)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.get("/profile/{uid}", response_model=UserStatsWithUserOut)
def query_user_profile(
    uid: str,
    user_service: UserService = Depends(get_user_service),
):
    """
    用户详情：
    - User 信息 + 关注数/粉丝数
    """
    try:
        profile = user_service.get_user_profile(
            uid=uid,
            to_dict=True,
        )
        if not profile:
            return BizResponse(data=None, msg=f"uid {uid} not found.", status_code=404)
        return BizResponse(data=profile)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.put("/info/id/{uid}", response_model=UserOut)
def update_user(
    uid: str,
    data: UserUpdate,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    普通用户更新自己的信息（不包含角色/状态）
    """
    try:
        updated = user_service.update_user(
            uid=uid,
            data=data,
            to_dict=True,
        )
        if not updated:
            return BizResponse(data=None, msg=f"uid {uid} not found.", status_code=404)
        return BizResponse(data=updated)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.put("/admin/id/{uid}", response_model=UserOut)
def admin_update_user(
    uid: str,
    data: AdminUserUpdate,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    管理员更新用户信息（可以修改角色/状态）
    """
    try:
        updated = user_service.admin_update_user(
            uid=uid,
            data=data,
            to_dict=True,
        )
        if not updated:
            return BizResponse(data=None, msg=f"uid {uid} not found.", status_code=404)
        return BizResponse(data=updated)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.put("/password/id/{uid}")
def change_password(
    uid: str,
    body: UserPasswordUpdate,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    修改密码（业务层会负责哈希和校验 old_password）
    """
    logger.debug("ok")
    try:
        ok = user_service.change_password(
            uid=uid,
            data=body,
        )
        if not ok:
            return BizResponse(data=False, msg="change password failed", status_code=400)
        return BizResponse(data=True)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except PasswordMismatchError as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)


@users_router.delete("/soft/id/{uid}")
def soft_delete_user(
    uid: str,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    软删除用户
    """
    try:
        ok = user_service.soft_delete_user(uid=uid)
        if not ok:
            return BizResponse(data=False, msg=f"soft delete faliled", status_code=404)
        return BizResponse(data=True)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)
    

@users_router.delete("/hard/id/{uid}")
def hard_deleted_user(
    uid: str,
    user_service: UserService = Depends(get_user_service),
):
    try:
        ok = user_service.hard_delete_user(uid=uid)
        if not ok:
            return BizResponse(data=False, msg=f"hard delete faliled", status_code=404)
        return BizResponse(data=True)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)


@users_router.get("/admin", response_model=BatchUsersAllOut)
def admin_get_users(
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    管理员：分页查看所有用户（包含软删）
    """
    try:
        result = user_service.admin_get_users(
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("[ADMIN] get users failed")
        return BizResponse(data=list(), msg=str(e), status_code=500)   


@users_router.get("/admin/id/{uid}", response_model=UserAllOut)
def admin_get_user_by_uid(
    uid: str,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    管理员根据 uid 获取用户详情：
    - 不过滤软删除
    - 返回 UserAllOut（字段更全）
    """
    try:
        user = user_service.admin_get_user_by_uid(
            uid=uid,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(user))
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception(f"[ADMIN] get user by uid failed: {e}")
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.get("/admin/username/{username}", response_model=BatchUsersAllOut)
def admin_get_users_by_username(
    username: str,
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    管理员根据用户名分页查询用户：
    - 不过滤软删除
    - 返回 BatchUsersAllOut
    """
    try:
        result = user_service.admin_get_users_by_username(
            username=username,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(f"[ADMIN] get users by username failed: {e}")
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.get("/admin/deleted", response_model=BatchUsersAllOut)
def admin_list_deleted_users(
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    管理员查看所有软删除用户：
    - deleted_at IS NOT NULL
    """
    try:
        result = user_service.admin_list_deleted_users(
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(f"[ADMIN] list deleted users failed: {e}")
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.get("/admin/abnormal-status", response_model=BatchUsersAllOut)
def admin_list_abnormal_status_users(
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service_basic),
):
    """
    管理员查看异常状态用户（冻结与禁用）：
    """
    try:
        result = user_service.admin_list_abnormal_status_users(
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(f"[ADMIN] list abnormal status users failed: {e}")
        return BizResponse(data=None, msg=str(e), status_code=500)
