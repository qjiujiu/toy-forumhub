from fastapi import APIRouter, Depends

from app.schemas.v2.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    BatchUsersOut,
    UserPasswordUpdate,
    AdminOperation,
)
from app.schemas.v2.user_stats import UserStatsWithUserOut
from app.service.v2.user_svc import UserService

from app.storage.v2.database import (
    get_user_repo,
)
from app.storage.v2.user.user_interface import IUserRepository

from app.core.exceptions import (
    UserNotFound,
    PasswordMismatchError,
    AdminPermissionDenied
)

from app.core.logx import logger
from app.core.biz_response import BizResponse


def get_user_service(
    user_repo: IUserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(user_repo)


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
        )
        return BizResponse(data=new_user)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)
    

@users_router.get("/", response_model=BatchUsersOut)
def query_batch_users(
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service),
):
    """
    分页获取用户列表（只含基础信息）
    """
    try:
        result = user_service.get_batch_users(
            page=page,
            page_size=page_size,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@users_router.get("/username/{username}", response_model=BatchUsersOut)
def get_users_by_username(
    username: str,
    page: int = 0,
    page_size: int = 10,
    user_service: UserService = Depends(get_user_service),
):
    """
    根据用户名分页查询同名用户
    """
    try:
        result = user_service.get_users_by_username(
            username=username,
            page=page,
            page_size=page_size,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@users_router.get("/id/{uid}", response_model=UserOut)
def query_user_basic(
    uid: str,
    user_service: UserService = Depends(get_user_service),
):
    """
    根据 uid 查询用户基础信息（不含关注/粉丝统计）
    """
    try:
        user = user_service.get_user_by_uid(
            uid=uid,
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
    user_service: UserService = Depends(get_user_service),
):
    """
    普通用户更新自己的信息（不包含角色/状态）
    """
    try:
        updated = user_service.update_user(
            uid=uid,
            data=data,
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
    user_service: UserService = Depends(get_user_service),
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
    user_service: UserService = Depends(get_user_service),
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
    

@users_router.delete("/hard")
def hard_deleted_user(
    body: AdminOperation,
    user_service: UserService = Depends(get_user_service),
):
    """
    管理员硬删除用户（仅管理员可操作）
    """
    try:
        ok = user_service.hard_delete_user(
            admin_uid=body.admin_uid,
            user_uid=body.user_uid,
        )
        if not ok:
            return BizResponse(data=False, msg="hard delete failed", status_code=404)
        return BizResponse(data=True)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)
    

@users_router.put("/admin/ban", response_model=UserOut)
def ban_user(
    body: AdminOperation,
    user_service: UserService = Depends(get_user_service),
):
    """
    管理员封禁用户：将用户 status 设置为 BANNED (1)
    """
    try:
        result = user_service.ban_user_by_uid(
            admin_uid=body.admin_uid,
            user_uid=body.user_uid,
        )
        if not result:
            return BizResponse(data=None, msg=f"user {body.user_uid} not found", status_code=404)
        return BizResponse(data=result)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.put("/admin/frozen", response_model=UserOut)
def frozen_user(
    body: AdminOperation,
    user_service: UserService = Depends(get_user_service),
):
    """
    管理员冻结用户：将用户 status 设置为 FROZEN (2)
    """
    try:
        result = user_service.frozen_user_by_uid(
            admin_uid=body.admin_uid,
            user_uid=body.user_uid,
        )
        if not result:
            return BizResponse(data=None, msg=f"user {body.user_uid} not found", status_code=404)
        return BizResponse(data=result)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.put("/admin/promote/admin", response_model=UserOut)
def promote_to_admin(
    body: AdminOperation,
    user_service: UserService = Depends(get_user_service),
):
    """
    管理员将用户升级为管理员：将用户 role 设置为 ADMIN (2)
    """
    try:
        result = user_service.user_to_admin(
            admin_uid=body.admin_uid,
            user_uid=body.user_uid,
        )
        if not result:
            return BizResponse(data=None, msg=f"user {body.user_uid} not found", status_code=404)
        return BizResponse(data=result)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@users_router.put("/admin/promote/moderator", response_model=UserOut)
def promote_to_moderator(
    body: AdminOperation,
    user_service: UserService = Depends(get_user_service),
):
    """
    管理员将用户升级为审核员：将用户 role 设置为 MODERATOR (1)
    """
    try:
        result = user_service.user_to_moderator(
            admin_uid=body.admin_uid,
            user_uid=body.user_uid,
        )
        if not result:
            return BizResponse(data=None, msg=f"user {body.user_uid} not found", status_code=404)
        return BizResponse(data=result)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)
