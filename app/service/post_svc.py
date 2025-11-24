from typing import Dict, Optional

from app.schemas.post import (
    PostCreate,
    PostOnlyCreate,
    PostOut,
    PostReviewOut,
    BatchPostsOut,
    PostUpdate,
    PostReviewUpdate,
    PostReviewStatus,
    PostReviewOut,
    BatchPostsReviewOut,
    PostAdminOut,
    BatchPostsAdminOut,
    PostGet,
)
from app.schemas.post_content import (
    PostContentCreate,
    PostContentOut,
)
from app.schemas.post_stats import (
    PostStatsCreate,
    PostStatsOut,
)

from app.storage.post.post_interface import IPostRepository
from app.storage.post_content.post_content_interface import IPostContentRepository
from app.storage.post_stats.post_stats_interface import IPostStatsRepository
from app.storage.user.user_interface import IUserRepository

from app.core.logx import logger
from app.core.exceptions import PostNotFound, InvalidReviewStatusTransition, UserNotFound


#---------------------------------------- 增 -----------------------------------------
def create_post(
    user_repo: IUserRepository,
    post_repo: IPostRepository,
    content_repo: IPostContentRepository,
    stats_repo: IPostStatsRepository,
    data: PostCreate,
    to_dict: bool = True,) -> Dict | PostOut:
    """
    创建帖子（业务接口）：
    1. 查看 用户ID 是否存在
    2. 在 posts 表创建一条记录
    3. 在 post_contents 表创建对应的标题 + 内容
    4. 在 post_stats 表创建统计记录（like_count=0, comment_count=0）
    5. 返回组装好的 PostOut
    """
    # 1. 查看 用户ID 是否存在
    user = user_repo.get_user_by_uid(data.author_id)
    if not user:
        raise UserNotFound(f"user {data.author_id} not found")
    
    # 2. 创建 posts 基本记录
    post_only = PostOnlyCreate(
        author_id=data.author_id,
        visibility=data.visibility,
        publish_status=data.publish_status,
    )
    pid = post_repo.create_post(post_only)
    logger.info(f"Created post pid={pid} for author={data.author_id}")

    # 3. 创建内容记录
    content_create = PostContentCreate(
        post_id=pid,
        title=data.title,
        content=data.content,
    )
    content_repo.create(content_create)
    logger.info(f"Created post_content for pid={pid}")

    # 4. 创建统计记录（点赞数、评论数初始化为 0）
    stats_create = PostStatsCreate(post_id=pid)
    stats_repo.create(stats_create)
    logger.info(f"Initialized post_stats for pid={pid}")

    # 5. 使用仓库封装的 get_post_by_pid 返回完整结构（含内容 + 统计）
    post_out = post_repo.author_get_post_by_pid(pid = pid, author_id= data.author_id)
    if not post_out:
        # 理论上不应该发生，防御性处理
        raise PostNotFound(f"post {pid} not found after creation")

    return post_out.model_dump() if to_dict else post_out


#------------------------------- 用户：查阅，更新，软删 ------------------------------------

def get_post_by_pid(post_repo: IPostRepository, pid: str, to_dict: bool = True,) -> Dict | Optional[PostOut]:
    """
    获取单个帖子详情（含内容 + 统计）
    """
    post = post_repo.viewer_get_post_by_pid(pid)
    if not post:
        return None
    return post.model_dump() if to_dict else post

def get_batch_posts(post_repo: IPostRepository, page: int = 0, page_size: int = 10, to_dict: bool = True,) -> Dict | BatchPostsOut:
    """
    分页获取帖子列表：
    - 按你的仓库实现默认为 _id 倒序
    - 包含每条的内容 + 统计
    """
    result = post_repo.get_batch_posts(page=page, page_size=page_size)
    return result.model_dump() if to_dict else result

def get_posts_by_author(user_repo: IUserRepository, post_repo: IPostRepository, data: PostGet, page: int = 0, page_size: int = 10, to_dict: bool = True,) -> Dict | BatchPostsOut:
    """
    根据作者 ID 分页获取该作者的所有帖子
    """
    current_user = user_repo.get_user_by_uid(data.current_user_id)
    if not current_user:
        raise UserNotFound(f"current user {data.current_user_id} not found")
    author = user_repo.get_user_by_uid(data.author_id)
    if not author:
        raise UserNotFound(f"author {data.author_id} not found")
    
    result = post_repo.get_posts_by_author(data=data, page=page, page_size=page_size,)
    return result.model_dump() if to_dict else result

def update_post(post_repo: IPostRepository, pid: str, data: PostUpdate) -> bool:
    """
    作者更新帖子：
    - 允许修改 visibility / publish_status
    - 审核状态不在这里改（专门的审核接口）
    """
    ok = post_repo.update_post(pid, data)
    if ok:
        logger.info(f"Updated post pid={pid} with data={data.model_dump(exclude_none=True)}")
    else:
        logger.warning(f"Update post failed, pid={pid} not found")
    return ok

def soft_delete_post(post_repo: IPostRepository, pid: str,) -> bool:
    """
    软删除帖子：
    - 仅设置 deleted_at，不真正删除记录
    - 级联逻辑由 ORM 或数据库层负责
    """
    ok = post_repo.soft_delete_post(pid)
    if ok:
        logger.info(f"Soft deleted post pid={pid}")
    else:
        logger.warning(f"Soft delete failed, post pid={pid} not found")
    return ok

#--------------------------------- 审核员：查阅，审核 --------------------------------------

def get_post_review(post_repo: IPostRepository, pid: str, to_dict: bool = True,) -> Dict | PostReviewOut:
    """
    通过帖子 ID 查询帖子审核信息（附带内容）：
    - 用于审核详情页
    """
    review = post_repo.get_post_review_by_pid(pid)
    if not review:
        raise PostNotFound(pid=pid)

    return review.model_dump() if to_dict else review


def get_post_reviews_by_author(post_repo: IPostRepository, author_id: str, page: int = 0, page_size: int = 10, to_dict: bool = True,) -> Dict | BatchPostsReviewOut:
    """
    审核员：通过作者 ID 查看该作者的所有帖子审核信息（包含所有审核状态）
    - 过滤 deleted_at（数据层 _review_query 已经做了）
    - 不过滤 review_status
    """
    result = post_repo.get_post_reviews_by_author(
        author_id=author_id,
        page=page,
        page_size=page_size,
    )

    # 一般不需要抛异常，查不到就返回空列表
    # 如果你希望作者不存在时报错，可以在这里补一层 User 校验

    return result.model_dump() if to_dict else result


def list_pending_review_posts(post_repo: IPostRepository, page: int = 0, page_size: int = 10, to_dict: bool = True,) -> Dict | BatchPostsReviewOut:
    """
    审核员 / 管理员：查看所有待审帖子列表
    - 只查 review_status = PENDING
    - 过滤 deleted_at
    """
    result = post_repo.list_pending_review_posts(
        page=page,
        page_size=page_size,
    )

    return result.model_dump() if to_dict else result


def review_post(post_repo: IPostRepository, pid: str, data: PostReviewUpdate, to_dict: bool = True,) -> Dict | PostReviewOut:
    """
    审核帖子：
    1. 读取当前帖子审核状态
    2. 校验状态流转是否合法（不允许从通过/拒绝回到待审）
    3. 更新审核状态 + 审核时间
    4. 返回 PostReviewOut
    """

    # 1. 获取当前帖子审核信息（附带内容）
    current = post_repo.get_post_review_by_pid(pid)
    if not current:
        raise PostNotFound(pid=pid)

    old_status = current.review_status
    new_status = data.review_status

    # 2. 校验状态流转
    # 不允许从 APPROVED/REJECTED 回到 PENDING
    if new_status == PostReviewStatus.PENDING and old_status != PostReviewStatus.PENDING:
        raise InvalidReviewStatusTransition(
            f"cannot change review_status from {old_status} back to PENDING"
        )

    # 你可以根据业务再细化，比如禁止 APPROVED <-> REJECTED 互相切
    # 这里只实现“不能回到待审”的规则

    # 3. 更新审核状态 & 审核时间（repo 内部会补 reviewed_at）
    ok = post_repo.update_review(pid, data)
    if not ok:
        # 极端情况：上一步还能查到，更新时却失败
        raise PostNotFound(f"post {pid} not found when updating review")

    # 5. 重新读取最新审核信息返回
    updated = post_repo.get_post_review_by_pid(pid)
    if not updated:
        # 正常不应该发生，防御性处理
        raise PostNotFound(f"post {pid} not found after review update")

    return updated.model_dump() if to_dict else updated


#---------------------------------- 管理员：查阅，硬删除 -------------------------------------

def admin_get_post_by_pid(post_repo: IPostRepository, pid: str, to_dict: bool = True,) -> Dict | PostAdminOut:
    """
    管理员根据帖子 ID 获取帖子详情：
    - 不过滤 deleted_at（软删除也能看）
    - 响应体为 PostAdminOut
    """
    post = post_repo.admin_get_post_by_pid(pid)
    if not post:
        raise PostNotFound(pid=pid)

    logger.info(f"[ADMIN] get post pid={pid}")
    return post.model_dump() if to_dict else post


def admin_list_all_posts(post_repo: IPostRepository, page: int = 0, page_size: int = 10, to_dict: bool = True,) -> Dict | BatchPostsAdminOut:
    """
    管理员查看所有帖子（含软删除）：
    - 不过滤 deleted_at
    - 分页返回 BatchPostsAdminOut
    """
    result = post_repo.admin_list_all_posts(
        page=page,
        page_size=page_size,
    )
    logger.info(
        f"[ADMIN] list all posts page={page}, page_size={page_size}, count={result.count}"
    )
    return result.model_dump() if to_dict else result


def admin_list_deleted_posts(post_repo: IPostRepository, page: int = 0, page_size: int = 10, to_dict: bool = True,) -> Dict | BatchPostsAdminOut:
    """
    管理员查看所有软删除帖子：
    - 只查 deleted_at IS NOT NULL
    """
    result = post_repo.admin_list_deleted_posts(
        page=page,
        page_size=page_size,
    )
    logger.info(
        f"[ADMIN] list deleted posts page={page}, page_size={page_size}, count={result.count}"
    )
    return result.model_dump() if to_dict else result


def admin_list_posts_by_author(post_repo: IPostRepository, author_id: str, page: int = 0, page_size: int = 10, to_dict: bool = True,) -> Dict | BatchPostsAdminOut:
    """
    管理员根据作者 ID 查看该作者的所有帖子（含软删）：
    - 不过滤 deleted_at
    """
    result = post_repo.admin_list_posts_by_author(
        author_id=author_id,
        page=page,
        page_size=page_size,
    )
    logger.info(
        f"[ADMIN] list posts by author author_id={author_id}, "
        f"page={page}, page_size={page_size}, count={result.count}"
    )
    return result.model_dump() if to_dict else result

def hard_delete_post(post_repo: IPostRepository, pid: str,) -> bool:
    """
    硬删除帖子：
    - 直接从 posts 表删除
    - 通过 cascade/delete-orphan 一并删除内容 + 统计等相关记录
    """
    ok = post_repo.hard_delete_post(pid)
    if ok:
        logger.info(f"Hard deleted post pid={pid}")
    else:
        logger.warning(f"Hard delete failed, post pid={pid} not found")
    return ok
