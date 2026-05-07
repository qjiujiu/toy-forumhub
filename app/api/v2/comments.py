from fastapi import APIRouter, Depends

from app.schemas.v2.comment import CommentCreate, CommentOut, BatchCommentsOut, CommentQueryDTO, StatusUpdate
from app.schemas.v2.post import PostOut
from app.service.v2.comment_svc import CommentService

from app.storage.v2.database import (
    get_comment_repo,
    get_post_repo,
    get_user_repo,
)
from app.storage.v2.comment.comment_interface import ICommentRepository
from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.user.user_interface import IUserRepository

from app.core.logx import logger
from app.core.biz_response import BizResponse
from app.core.exceptions import CommentNotFound, AdminPermissionDenied, UserNotFound


def get_comment_service(
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    post_repo: IPostRepository = Depends(get_post_repo),
    user_repo: IUserRepository = Depends(get_user_repo),
) -> CommentService:
    return CommentService(comment_repo, post_repo, user_repo)


comments_router = APIRouter(prefix="/comments", tags=["comments"])


@comments_router.post("/", response_model=CommentOut)
def create_comment(
    comment: CommentCreate,
    comment_service: CommentService = Depends(get_comment_service),
):
    try:
        new_comment = comment_service.create_comment(comment, to_dict=True)
        return BizResponse(data=new_comment)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)


@comments_router.get("/id/{cid}", response_model=CommentOut)
def get_comment(
    cid: str,
    comment_service: CommentService = Depends(get_comment_service),
):
    comment = comment_service.get_comment(cid)
    if not comment:
        return BizResponse(data=None, msg="comment not found", status_code=404)
    return BizResponse(data=comment)


@comments_router.get("/post/{post_id}", response_model=BatchCommentsOut)
def get_comments_by_post(
    post_id: str,
    page: int = 0,
    page_size: int = 20,
    comment_service: CommentService = Depends(get_comment_service),
):
    """按帖子 ID 获取评论列表。"""
    result = comment_service.get_comments_by_post_id(post_id, page, page_size)
    return BizResponse(data=result)


@comments_router.get("/author/{author_id}", response_model=BatchCommentsOut)
def get_comments_by_author(
    author_id: str,
    page: int = 0,
    page_size: int = 20,
    comment_service: CommentService = Depends(get_comment_service),
):
    """按作者 ID 获取评论列表。"""
    result = comment_service.get_comments_by_author_id(author_id, page, page_size)
    return BizResponse(data=result)


@comments_router.get("/root/{root_id}", response_model=BatchCommentsOut)
def get_comments_by_root(
    root_id: str,
    page: int = 0,
    page_size: int = 20,
    comment_service: CommentService = Depends(get_comment_service),
):
    """按根评论 ID 获取楼中楼完整线程。"""
    result = comment_service.get_comments_by_root_id(root_id, page, page_size)
    return BizResponse(data=result)


@comments_router.get("/parent/{parent_id}", response_model=BatchCommentsOut)
def get_comments_by_parent(
    parent_id: str,
    page: int = 0,
    page_size: int = 20,
    comment_service: CommentService = Depends(get_comment_service),
):
    """按父评论 ID 获取直接子回复。"""
    result = comment_service.get_comments_by_parent_id(parent_id, page, page_size)
    return BizResponse(data=result)


@comments_router.get("/top", response_model=BatchCommentsOut)
def get_comments_top(
    post_id: str,
    page: int = 0,
    page_size: int = 20,
    comment_service: CommentService = Depends(get_comment_service),
):
    """获取某帖子下的一级评论（parent_id IS NULL）。"""
    result = comment_service.get_comments_by_parent_id(None, page, page_size)
    return BizResponse(data=result)


@comments_router.patch("/id/{cid}")
def update_comment(
    cid: str,
    data: StatusUpdate,
    admin_uid: str,
    comment_service: CommentService = Depends(get_comment_service),
):
    try:
        success = comment_service.update_comment(admin_uid, cid, data)
        if not success:
            return BizResponse(data=False, msg="update failed", status_code=500)
        return BizResponse(data=True)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)


@comments_router.delete("/id/{cid}")
def delete_comment(
    cid: str,
    comment_service: CommentService = Depends(get_comment_service),
):
    success = comment_service.delete_comment(cid)
    if not success:
        return BizResponse(data=False, msg="delete failed", status_code=500)
    return BizResponse(data=True)


@comments_router.delete("/hard/{cid}")
def hard_delete_comment(
    cid: str,
    admin_uid: str,
    comment_service: CommentService = Depends(get_comment_service),
):
    try:
        ok = comment_service.hard_delete_comment(admin_uid, cid)
        return BizResponse(data=ok)
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except AdminPermissionDenied as e:
        return BizResponse(data=None, msg=str(e), status_code=403)
    except Exception as e:
        return BizResponse(data=False, msg=str(e), status_code=500)


@comments_router.get("/post-by-cid/{cid}", response_model=PostOut)
def get_post_by_comment_cid(
    cid: str,
    comment_service: CommentService = Depends(get_comment_service),
):
    try:
        post = comment_service.get_post_by_comment_cid(cid, to_dict=True)
        return BizResponse(data=post)
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        return BizResponse(data=None, msg=str(e), status_code=500)