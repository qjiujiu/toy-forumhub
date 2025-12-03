from fastapi import APIRouter, Depends

from app.schemas.post import (
    PostCreate,
    PostOut,
    BatchPostsOut,
    PostUpdate,
    PostReviewOut,
    BatchPostsReviewOut,
    PostAdminOut,
    BatchPostsAdminOut,
    PostReviewUpdate,
    PostGet
)
from app.core.biz_response import BizResponse
from app.service import post_svc

from app.storage.database import (
    get_user_repo,
    get_post_repo,
    get_postcon_repo,
    get_poststats_repo,
)
from app.storage.post.post_interface import IPostRepository
from app.storage.post_content.post_content_interface import IPostContentRepository
from app.storage.post_stats.post_stats_interface import IPostStatsRepository
from app.storage.user.user_interface import IUserRepository

from app.core.exceptions import PostNotFound, InvalidReviewStatusTransition, UserNotFound, ForbiddenAction
from app.core.logx import logger
from fastapi.encoders import jsonable_encoder

posts_router = APIRouter(prefix="/posts", tags=["posts"])


# --------------------------------- 创建帖子 ---------------------------------
@posts_router.post("/", response_model=PostOut)
def create_post(
    payload: PostCreate,
    user_repo: IUserRepository = Depends(get_user_repo),
    post_repo: IPostRepository = Depends(get_post_repo),
    content_repo: IPostContentRepository = Depends(get_postcon_repo),
    stats_repo: IPostStatsRepository = Depends(get_poststats_repo),
):
    """
    创建帖子：
    - 在 posts 表创建记录
    - 在 post_contents 表创建内容
    - 在 post_stats 表创建统计记录
    """
    try:
        post = post_svc.create_post(
            user_repo=user_repo,
            post_repo=post_repo,
            content_repo=content_repo,
            stats_repo=stats_repo,
            data=payload,
            to_dict=True,
        )
        return BizResponse(data=post)
    except PostNotFound as e:
        # 理论上 create_post 最后查不到才会抛这个
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)
    except UserNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


# ---------------------------------用户：查询帖子，更新帖子，软删除帖子 ---------------------------------
@posts_router.get("/user/{pid}", response_model=PostOut)
def get_post(
    pid: str,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    通过帖子 ID 获取帖子详情（含内容 + 统计）
    """
    try:
        post = post_svc.get_post_by_pid(
            post_repo=post_repo,
            pid=pid,
            to_dict=True,
        )
        if not post:
            return BizResponse(data=None, msg=f"post {pid} not found", status_code=404)
        return BizResponse(data=jsonable_encoder(post))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/", response_model=BatchPostsOut)
def list_posts(
    page: int = 0,
    page_size: int = 10,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    分页获取帖子列表（对外可见的帖子）
    """
    try:
        result = post_svc.get_batch_posts(
            post_repo=post_repo,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/author/", response_model=BatchPostsOut)
def list_posts_by_author(
    data: PostGet,
    page: int = 0,
    page_size: int = 10,
    user_repo: IUserRepository = Depends(get_user_repo),
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    根据作者 ID 分页获取该作者的帖子列表
    （当前实现为“访客视角”，只返回对外可见的帖子）
    """
    try:
        result = post_svc.get_posts_by_author(
            user_repo=user_repo,
            post_repo=post_repo,
            data=data,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.put("/status/pid/{pid}")
def update_post(
    pid: str,
    payload: PostUpdate,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    作者更新帖子：
    - 只允许更新 visibility / publish_status
    - 审核状态不在这里修改
    """
    try:
        ok = post_svc.update_post(
            post_repo=post_repo,
            pid=pid,
            data=payload,
        )
        if not ok:
            return BizResponse(data=False, msg=f"post {pid} not found", status_code=404)
        return BizResponse(data=True)
    except ForbiddenAction as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=False, msg=str(e), status_code=500)


@posts_router.delete("/soft/pid/{pid}")
def soft_delete_post(
    pid: str,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    软删除帖子：
    - 设置 deleted_at，不真正删除记录
    """
    try:
        ok = post_svc.soft_delete_post(
            post_repo=post_repo,
            pid=pid,
        )
        if not ok:
            return BizResponse(data=False, msg=f"post {pid} not found", status_code=404)
        return BizResponse(data=True)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=False, msg=str(e), status_code=500)
    

# ========================= 审核相关接口（审核员 / 管理员） =========================

@posts_router.get("/review/pid/{pid}", response_model=PostReviewOut)
def get_post_review(
    pid: str,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    审核详情：通过帖子 ID 查询帖子审核信息（附带内容）
    """
    try:
        review = post_svc.get_post_review(
            post_repo=post_repo,
            pid=pid,
            to_dict=True,
        )
        return BizResponse(data=review)
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/review/author/{author_id}", response_model=BatchPostsReviewOut)
def list_post_reviews_by_author(
    author_id: str,
    page: int = 0,
    page_size: int = 10,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    审核员：通过作者 ID 查看该作者的所有帖子审核信息（包含所有审核状态）
    """
    try:
        result = post_svc.get_post_reviews_by_author(
            post_repo=post_repo,
            author_id=author_id,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/review/pending", response_model=BatchPostsReviewOut)
def list_pending_review_posts(
    page: int = 0,
    page_size: int = 10,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    审核员 / 管理员：查看所有待审帖子列表
    """
    try:
        result = post_svc.list_pending_review_posts(
            post_repo=post_repo,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.put("/review/pid/{pid}", response_model=PostReviewOut)
def review_post(
    pid: str,
    payload: PostReviewUpdate,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    审核帖子：
    - 更新 review_status（并自动写入 reviewed_at）
    - 不允许从 通过/拒绝 回到 待审
    """
    try:
        result = post_svc.review_post(
            post_repo=post_repo,
            pid=pid,
            data=payload,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except InvalidReviewStatusTransition as e:
        return BizResponse(data=None, msg=str(e), status_code=400)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


# ========================= 管理员接口（最高权限） =========================

@posts_router.get("/admin/pid/{pid}", response_model=PostAdminOut)
def admin_get_post(
    pid: str,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    管理员：根据帖子 ID 查看帖子详情
    - 包含软删除帖子
    - 返回 PostAdminOut（包含审核状态、可见性、发布状态、deleted_at 等）
    """
    try:
        post = post_svc.admin_get_post_by_pid(
            post_repo=post_repo,
            pid=pid,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(post))
    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/admin", response_model=BatchPostsAdminOut)
def admin_list_all_posts(
    page: int = 0,
    page_size: int = 10,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    管理员：查看所有帖子（含软删除）
    """
    try:
        result = post_svc.admin_list_all_posts(
            post_repo=post_repo,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/admin/deleted", response_model=BatchPostsAdminOut)
def admin_list_deleted_posts(
    page: int = 0,
    page_size: int = 10,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    管理员：查看所有软删除的帖子
    """
    try:
        result = post_svc.admin_list_deleted_posts(
            post_repo=post_repo,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.get("/admin/author/{author_id}", response_model=BatchPostsAdminOut)
def admin_list_posts_by_author(
    author_id: str,
    page: int = 0,
    page_size: int = 10,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    管理员：根据作者 ID 查看该作者的所有帖子（含软删）
    """
    try:
        result = post_svc.admin_list_posts_by_author(
            post_repo=post_repo,
            author_id=author_id,
            page=page,
            page_size=page_size,
            to_dict=True,
        )
        return BizResponse(data=jsonable_encoder(result))
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=None, msg=str(e), status_code=500)


@posts_router.delete("/admin/hard/{pid}")
def admin_hard_delete_post(
    pid: str,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    管理员：硬删除帖子
    - 直接从 posts 表移除
    - 依赖 ORM cascade 删除内容 / 统计 / 评论等
    """
    try:
        ok = post_svc.hard_delete_post(
            post_repo=post_repo,
            pid=pid,
        )
        if not ok:
            return BizResponse(data=False, msg=f"post {pid} not found", status_code=404)
        return BizResponse(data=True)
    except Exception as e:
        logger.exception(e)
        return BizResponse(data=False, msg=str(e), status_code=500)
    
@posts_router.put("/admin/restore/{pid}")
def admin_restore_post(
    pid: str,
    post_repo: IPostRepository = Depends(get_post_repo),
):
    """
    管理员恢复软删除帖子：
    - 必须是软删除状态才能恢复
    - 未软删除 → 返回 False
    - 帖子不存在 → 404
    """
    try:
        ok = post_svc.restore_post(
            post_repo=post_repo,
            pid=pid,
        )

        if not ok:
            # 存在但未软删除，属于业务无效操作
            return BizResponse(data=False, msg=f"post {pid} is not soft-deleted", status_code=400,)

        return BizResponse(data=True)

    except PostNotFound as e:
        return BizResponse(data=None, msg=str(e), status_code=404)
    except Exception as e:
        logger.exception("admin_restore_post error")
        return BizResponse(data=None, msg=str(e),status_code=500)