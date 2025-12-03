from fastapi import APIRouter, Depends

from app.schemas.comment import (
    CommentCreate,
    CommentOut,
    CommentAdminOut,
    BatchCommentsOut,
    BatchCommentsAdminOut,
    ReviewUpdate,
    StatusUpdate,
)
from app.core.biz_response import BizResponse
from app.service import comment_svc

from app.storage.database import (
    get_user_repo,
    get_post_repo,
    get_comment_repo,
    get_comcon_repo,
    get_poststats_repo,
)
from app.storage.user.user_interface import IUserRepository
from app.storage.post.post_interface import IPostRepository
from app.storage.comment.comment_interface import ICommentRepository
from app.storage.post_stats.post_stats_interface import IPostStatsRepository
from app.storage.comment_content.comment_content_interface import ICommentContentRepository

from app.core.exceptions import (
    UserNotFound,
    PostNotFound,
    CommentNotFound,
    InvalidReviewStatusTransition,
)
from app.core.logx import logger
from fastapi.encoders import jsonable_encoder

comments_router = APIRouter(prefix="/comments", tags=["comments"])

@comments_router.post("/", response_model=CommentOut)
def create_comment(
    data: CommentCreate,
    user_repo: IUserRepository = Depends(get_user_repo),
    post_repo: IPostRepository = Depends(get_post_repo),
    stats_repo: IPostStatsRepository = Depends(get_poststats_repo),
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    content_repo: ICommentContentRepository = Depends(get_comcon_repo),
):
    """
    创建评论：
    - 校验用户是否存在
    - 校验帖子是否存在（访客可见）
    - 创建评论记录 + 评论内容记录
    """
    try:
        new_comment = comment_svc.create_comment(
            user_repo=user_repo,
            post_repo=post_repo,
            stats_repo=stats_repo,
            comment_repo=comment_repo,
            content_repo=content_repo,
            data=data,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(new_comment))
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception("create_comment error")
        return BizResponse(data=None, msg=str(e), status_code=500)

@comments_router.get("/{cid}", response_model=CommentOut)
def get_comment(
    cid: str,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    获取单条评论（用户视角）：
    - 不返回软删 / 折叠 / 审核拒绝的评论
    """
    try:
        comment = comment_svc.get_comment_for_user(
            comment_repo=comment_repo,
            cid=cid,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(comment))
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception("get_comment error")
        return BizResponse(data=None, msg=str(e), status_code=500)

@comments_router.get("/admin/{cid}", response_model=CommentAdminOut)
def admin_get_comment(
    cid: str,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    管理员查看单条评论：
    - 可以看到软删除 / 折叠 / 审核拒绝等所有状态
    """
    try:
        comment = comment_svc.get_comment_for_admin(
            comment_repo=comment_repo,
            cid=cid,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(comment))
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception("admin_get_comment error")
        return BizResponse(data=None, msg=str(e), status_code=500)


@comments_router.get("/thread/{cid}", response_model=BatchCommentsOut)
def get_comment_thread(
    cid: str,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    查看某条评论所在整组对话（基于 root_id）——用户视角
    """
    try:
        result = comment_svc.get_comment_thread_for_user(
            comment_repo=comment_repo,
            cid=cid,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception("get_comment_thread error")
        return BizResponse(data=None, msg=str(e), status_code=500)


@comments_router.get("/subtree/{cid}", response_model=BatchCommentsOut)
def get_comment_subtree(
    cid: str,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    查看从某条评论开始的子树对话（只看这一支）——用户视角
    """
    try:
        result = comment_svc.get_comment_subtree_for_user(
            comment_repo=comment_repo,
            cid=cid,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception("get_comment_subtree error")
        return BizResponse(data=None, msg=str(e), status_code=500)

@comments_router.get("/post/{post_id}", response_model=BatchCommentsOut)
def list_comments_by_post_for_user(
    post_id: str,
    page: int = 0,
    page_size: int = 10,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    普通用户 / 前台：
    - 查看某帖子的评论列表，只返回一级评论（不含软删 / 折叠 / 审核拒绝）
    """
    try:
        result = comment_svc.list_comments_by_post_for_user(
            comment_repo=comment_repo,
            post_id=post_id,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("list_comments_by_post_for_user error")
        # 返回空列表结构
        return BizResponse(data={"total": 0, "count": 0, "items": []}, msg=str(e), status_code=500)


@comments_router.get("/review/post/{post_id}", response_model=BatchCommentsAdminOut)
def list_comments_by_post_for_reviewer(
    post_id: str,
    page: int = 0,
    page_size: int = 10,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    审核员：
    - 查看某帖子的所有审核状态评论（PENDING / APPROVED / REJECTED）
    - 不含软删
    """
    try:
        result = comment_svc.list_comments_by_post_for_reviewer(
            comment_repo=comment_repo,
            post_id=post_id,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("list_comments_by_post_for_reviewer error")
        return BizResponse(data={"total": 0, "count": 0, "items": []}, msg=str(e), status_code=500)


@comments_router.get("/admin/post/{post_id}", response_model=BatchCommentsAdminOut)
def list_comments_by_post_for_admin(
    post_id: str,
    page: int = 0,
    page_size: int = 10,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    管理员：
    - 查看某帖子的所有评论（含软删除、折叠、REJECTED）
    """
    try:
        result = comment_svc.list_comments_by_post_for_admin(
            comment_repo=comment_repo,
            post_id=post_id,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception("list_comments_by_post_for_admin error")
        return BizResponse(data={"total": 0, "count": 0, "items": []}, msg=str(e), status_code=500)


@comments_router.put("/review/{cid}", response_model=CommentAdminOut)
def review_comment(
    cid: str,
    data: ReviewUpdate,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    审核评论：
    - 修改 review_status（PENDING / APPROVED / REJECTED）
    - 不允许从通过/拒绝回到待审
    """
    try:
        updated = comment_svc.review_comment(
            comment_repo=comment_repo,
            cid=cid,
            data=data,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(updated))
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except InvalidReviewStatusTransition as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception("review_comment error")
        return BizResponse(data=None, msg=str(e), status_code=500)


@comments_router.put("/admin/status/{cid}", response_model=CommentAdminOut)
def update_comment_status(
    cid: str,
    data: StatusUpdate,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    管理员更新评论显示状态：
    - 折叠 / 取消折叠（status 字段）
    """
    try:
        updated = comment_svc.update_comment_status(
            comment_repo=comment_repo,
            cid=cid,
            data=data,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(updated))
    except CommentNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except InvalidReviewStatusTransition as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception("update_comment_status error")
        return BizResponse(data=None, msg=str(e), status_code=500)


@comments_router.delete("/soft/{cid}")
def soft_delete_comment(
    cid: str,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    stats_repo: IPostStatsRepository = Depends(get_poststats_repo),
):
    """
    普通用户软删除评论：
    - 实际为设置 deleted_at
    - 是否只能删除自己的评论，由上层鉴权控制
    """
    try:
        ok = comment_svc.soft_delete_comment(
            comment_repo=comment_repo,
            stats_repo=stats_repo,
            cid=cid,
        )
        if not ok:
            return BizResponse(data=False, msg="comment not found", status_code=404)
        return BizResponse(data=True)
    except Exception as e:
        logger.exception("soft_delete_comment error")
        return BizResponse(data=False, msg=str(e), status_code=500)


@comments_router.post("/admin/restore/{cid}", response_model=CommentAdminOut)
def restore_comment_api(
    cid: str,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    stats_repo: IPostStatsRepository = Depends(get_poststats_repo),
):
    """
    管理员恢复已软删除的评论
    """
    try:
        ok = comment_svc.restore_comment(
            comment_repo=comment_repo,
            stats_repo=stats_repo,
            cid=cid,
        )
        if not ok:
            return BizResponse(data=None, msg="comment not found or not soft-deleted", status_code=404)

        restored = comment_repo.get_comment_by_cid_for_admin(cid)
        return BizResponse(data=jsonable_encoder(restored))

    except Exception as e:
        logger.exception("restore_comment error")
        return BizResponse(data=None, msg=str(e), status_code=500)


# 因为涉及评论数的更新，所以在硬删除之前需要软删除，用户使用的删除都是软删除，管理员可以定期硬删除已经软删除的评论
@comments_router.delete("/hard/{cid}")
def hard_delete_comment(
    cid: str,
    comment_repo: ICommentRepository = Depends(get_comment_repo),
):
    """
    管理员硬删除评论：
    - 直接删除 comments 记录
    - 通过 cascade 一并删除 CommentContent 等
    """
    try:
        ok = comment_svc.hard_delete_comment(
            comment_repo=comment_repo,
            cid=cid,
        )
        if not ok:
            return BizResponse(data=False, msg="comment not found", status_code=404)
        return BizResponse(data=True)
    except Exception as e:
        logger.exception("hard_delete_comment error")
        return BizResponse(data=False, msg=str(e), status_code=500)


