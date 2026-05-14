from typing import Optional
from fastapi import APIRouter, Depends

from app.schemas.v2.post import PostCreate, PostOut, BatchPostsOut, PostUpdate, TopPostsResponse
from app.schemas.v2.post_content import PostContentUpdate
from app.service.v2.post_svc import PostService

from app.storage.v2.database import (
    get_post_repo,
    get_user_repo,
)
from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.user.user_interface import IUserRepository

from app.kit.exceptions import PostNotFound, ForbiddenAction, AdminPermissionDenied

import logging
logger = logging.getLogger(__name__)
from app.schemas.v2.biz_response import BizResponse


def get_post_service(
    post_repo: IPostRepository = Depends(get_post_repo),
    user_repo: IUserRepository = Depends(get_user_repo),
) -> PostService:
    return PostService(post_repo, user_repo)


posts_router = APIRouter(prefix="/posts", tags=["posts"])


@posts_router.post("/", response_model=PostOut)
def create_post(
    post: PostCreate,
    post_service: PostService = Depends(get_post_service),
):
    try:
        new_post = post_service.create_post(post, to_dict=True)
        return BizResponse(data=new_post)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/", response_model=BatchPostsOut)
def get_all_posts(
    page: int = 0,
    page_size: int = 10,
    post_service: PostService = Depends(get_post_service),
):
    """
    分页获取所有帖子（按创建时间倒序）
    """
    try:
        result = post_service.get_all_posts(page=page, page_size=page_size, to_dict=True)
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@posts_router.get("/id/{pid}", response_model=PostOut)
def get_post(
    pid: str,
    post_service: PostService = Depends(get_post_service),
):
    try:
        post = post_service.get_post(pid, to_dict=True)
        return BizResponse(data=post)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/author/{author_id}/{current_uid}", response_model=BatchPostsOut)
def get_posts_by_author(
    author_id: str,
    current_uid: Optional[str] = None,
    page: int = 0,
    page_size: int = 10,
    post_service: PostService = Depends(get_post_service),
):
    try:
        result = post_service.get_posts_by_author(
            author_id=author_id,
            current_uid=current_uid,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=result)
    except Exception as e:
        return BizResponse(data=list(), msg=str(e), status_code=500)


@posts_router.put("/content/{pid}/{uid}", response_model=PostOut)
def update_post_content(
    pid: str,
    uid: str,
    body: PostContentUpdate,
    post_service: PostService = Depends(get_post_service),
):
    try:
        updated = post_service.update_post_content(uid, pid, body, to_dict=True)
        return BizResponse(data=updated)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except ForbiddenAction as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.put("/visibility/{pid}/{uid}", response_model=PostOut)
def update_post_visibility(
    pid: str,
    uid: str,
    body: PostUpdate,
    post_service: PostService = Depends(get_post_service),
):
    try:
        updated = post_service.update_post_visibility(uid, pid, body, to_dict=True)
        return BizResponse(data=updated)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except ForbiddenAction as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.put("/publish/{pid}/{uid}", response_model=PostOut)
def publish_post(
    pid: str,
    uid: str,
    post_service: PostService = Depends(get_post_service),
):
    try:
        updated = post_service.publish_post(uid, pid, to_dict=True)
        return BizResponse(data=updated)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except ForbiddenAction as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.delete("/soft/{pid}/{uid}")
def soft_delete_post(
    pid: str,
    uid: str,
    post_service: PostService = Depends(get_post_service),
):
    try:
        ok = post_service.soft_delete_post(uid, pid)
        return BizResponse(data=ok)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except ForbiddenAction as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)


@posts_router.delete("/hard/{pid}/{admin_uid}")
def hard_delete_post(
    pid: str,
    admin_uid: str,
    post_service: PostService = Depends(get_post_service),
):
    try:
        ok = post_service.hard_delete_post(admin_uid, pid)
        return BizResponse(data=ok)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)


@posts_router.put("/ban/{pid}/{admin_uid}", response_model=PostOut)
def ban_post(
    pid: str,
    admin_uid: str,
    post_service: PostService = Depends(get_post_service),
):
    try:
        result = post_service.ban_post(admin_uid, pid, to_dict=True)
        return BizResponse(data=result)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/top/liked", response_model=TopPostsResponse)
def get_top_liked_posts(
    limit: int = 10,
    post_service: PostService = Depends(get_post_service),
):
    try:
        items = post_service.get_top_liked_posts(limit=limit, to_dict=True)
        return BizResponse(data={"items": items})
    except Exception as e:
        return BizResponse(data={"items": []}, msg=str(e), status_code=500)


@posts_router.get("/top/commented", response_model=TopPostsResponse)
def get_top_commented_posts(
    limit: int = 10,
    post_service: PostService = Depends(get_post_service),
):
    try:
        items = post_service.get_top_commented_posts(limit=limit, to_dict=True)
        return BizResponse(data={"items": items})
    except Exception as e:
        return BizResponse(data={"items": []}, msg=str(e), status_code=500)