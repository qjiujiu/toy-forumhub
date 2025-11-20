from fastapi import APIRouter, Depends

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    AdminUserUpdate,
    UserOut,
    BatchUsersOut,
    UserPasswordUpdate,
)
from app.schemas.user_stats import UserStatsWithUserOut
from app.schemas.follow import BatchFollowsOut

from app.core.biz_response import BizResponse
from app.service import user_svc

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

users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.post("/", response_model=UserOut)
def create_user(user: UserCreate, user_repo: IUserRepository = Depends(get_user_repo), stats_repo: IUserStatsRepository = Depends(get_usersta_repo),):
    """
    创建用户：
    - 创建 user 表记录
    - 初始化 user_statistics（关注数/粉丝数为 0）
    """
    try:
        new_user = user_svc.create_user(
            user_repo=user_repo,
            stats_repo=stats_repo,
            user_data=user,
            to_dict=True,
        )
        return BizResponse(data=new_user)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)
    

@users_router.get("/", response_model=BatchUsersOut)
def query_batch_users(page: int = 0, page_size: int = 10, user_repo: IUserRepository = Depends(get_user_repo)):
    """
    分页获取用户列表（只含基础信息）
    """
    try:
        result = user_svc.get_batch_users(
            user_repo=user_repo,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@users_router.get("/username/{username}", response_model=BatchUsersOut)
def get_users_by_username(username: str, page: int = 0, page_size: int = 10, user_repo: IUserRepository = Depends(get_user_repo)):
    """
    根据用户名分页查询同名用户
    """
    try:
        result = user_svc.get_users_by_username(
            user_repo=user_repo,
            username=username,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@users_router.get("/id/{uid}", response_model=UserOut)
def query_user_basic(uid: str, user_repo: IUserRepository = Depends(get_user_repo)):
    """
    根据 uid 查询用户基础信息（不含关注/粉丝统计）
    """
    try:
        user = user_svc.get_user_by_uid(
            user_repo=user_repo,
            uid=uid,
            to_dict=True,
        )
        return BizResponse(data=user)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)

# TODO 返回用户详细信息，待完善

@users_router.get("/profile/{uid}", response_model=UserStatsWithUserOut)
def query_user_profile(uid: str, stats_repo: IUserStatsRepository = Depends(get_usersta_repo)):
    """
    用户详情：
    - User 信息 + 关注数/粉丝数
    """
    try:
        profile = user_svc.get_user_profile(
            stats_repo=stats_repo,
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
def update_user(uid: str, data: UserUpdate, user_repo: IUserRepository = Depends(get_user_repo)):
    """
    普通用户更新自己的信息（不包含角色/状态）
    """
    try:
        updated = user_svc.update_user(
            user_repo=user_repo,
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
def admin_update_user(uid: str, data: AdminUserUpdate, user_repo: IUserRepository = Depends(get_user_repo)):
    """
    管理员更新用户信息（可以修改角色/状态）
    """
    try:
        updated = user_svc.admin_update_user(
            user_repo=user_repo,
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
def change_password(uid: str, body: UserPasswordUpdate, user_repo: IUserRepository = Depends(get_user_repo),):
    """
    修改密码（业务层会负责哈希和校验 old_password）
    """
    logger.debug("ok")
    try:
        ok = user_svc.change_password(
            user_repo=user_repo,
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
def soft_delete_user(uid: str, user_repo: IUserRepository = Depends(get_user_repo)):
    """
    软删除用户
    """
    try:
        ok = user_svc.soft_delete_user(
            user_repo=user_repo,
            uid=uid,
        )
        if not ok:
            return BizResponse(data=False, msg=f"soft delete faliled", status_code=404)
        return BizResponse(data=True)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)
    
# 只有管理员可以使用的硬删除接口
@users_router.delete("/hard/id/{uid}")
def hard_deleted_user(uid: str, user_repo: IUserRepository = Depends(get_user_repo)):
    try:
        ok = user_svc.hard_delete_user(
            user_repo=user_repo,
            uid=uid,
        )
        if not ok:
            return BizResponse(data=False, msg=f"hard delete faliled", status_code=404)
        return BizResponse(data=True)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)