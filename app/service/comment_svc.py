from typing import Dict, Optional

from app.schemas.comment import (
    CommentCreate,
    CommentOnlyCreate,
    CommentOut,
    CommentAdminOut,
    BatchCommentsOut,
    BatchCommentsAdminOut,
    ReviewUpdate,
    StatusUpdate,
)
from app.schemas.comment_content import (
    CommentContentCreate,
)
from app.storage.comment.comment_interface import ICommentRepository
from app.storage.comment_content.comment_content_interface import ICommentContentRepository
from app.storage.user.user_interface import IUserRepository
from app.storage.post.post_interface import IPostRepository
from app.storage.post_stats.post_stats_interface import IPostStatsRepository

from app.core.logx import logger
from app.core.exceptions import (
    UserNotFound,
    PostNotFound,
    CommentNotFound,
    InvalidReviewStatusTransition,
    CommentNotSoftDeletedError,
)
from app.models.comment import ReviewStatus
from collections import defaultdict

#---------------------------------------- 增 -----------------------------------------

def create_comment(
    user_repo: IUserRepository,
    post_repo: IPostRepository,
    comment_repo: ICommentRepository,
    content_repo: ICommentContentRepository,
    stats_repo: IPostStatsRepository,          
    data: CommentCreate,
    to_dict: bool = True,
) -> Dict | CommentOut:
    """
    创建评论（业务接口）：
    1. 校验用户是否存在
    2. 校验帖子是否存在（且对当前业务来说允许被评论）
    3. 在 comments 表创建一条记录
    4. 在 comment_contents 表创建对应的正文内容
    5. 在 post_stats 表中将 comment_count + 1
    6. 返回组装好的 CommentOut
    """

    # 1. 校验用户是否存在
    user = user_repo.get_user_by_uid(data.author_id)
    if not user:
        raise UserNotFound(message = f"user {data.author_id} not found")
    
    # 2. 校验帖子是否存在（这里使用访客可见的查询，表示只能给正常公开帖评论）
    post = post_repo.viewer_get_post_by_pid(data.post_id)
    if not post:
        raise PostNotFound(message = f"post {data.post_id} not found")

    # 3. 创建 comments 基本记录
    comment_only = CommentOnlyCreate(
        post_id=data.post_id,
        author_id=data.author_id,
        parent_id=data.parent_id,
        root_id=data.root_id,      # 如果你想在这里补 root_id，也可以后续再做
        status=None,               # 使用模型默认 NORMAL
        review_status=None,        # 使用模型默认 PENDING
    )
    cid = comment_repo.create_comment(comment_only)
    logger.info(f"Created comment cid={cid} on post={data.post_id} by author={data.author_id}")

    # 4. 创建评论内容记录
    content_create = CommentContentCreate(
        comment_id=cid,
        content=data.content,
    )
    content_repo.create(content_create)
    logger.info(f"Created comment_content for cid={cid}")

    # 5. 更新帖子统计信息：评论数 +1
    stats_repo.update_comments(post_id=data.post_id, step=1)
    logger.info(f"Incremented comment_count for post_id={data.post_id}")

    # 二级评论
    if data.parent_id == data.root_id:
        comment_repo.update_comment_count(cid=data.parent_id, step=1)
    
    # 三级即更多评论
    if data.parent_id and data.parent_id != data.root_id:
         comment_repo.update_comment_count(cid=data.parent_id, step=1)
         comment_repo.update_comment_count(cid=data.root_id, step=1)

    # 6. 返回完整的评论信息（用户可见视角）
    comment_out = comment_repo.get_comment_by_cid_for_user(cid)
    if not comment_out:
        # 理论上不应该发生，防御性处理
        raise CommentNotFound(message=f"comment {cid} not found after creation")

    return comment_out.model_dump() if to_dict else comment_out

#------------------------------- 查询：单条评论 ------------------------------------

def get_comment_for_user(
    comment_repo: ICommentRepository,
    cid: str,
    to_dict: bool = True,
) -> Dict | CommentOut:
    """
    普通用户 / 前台：查看单条评论
    - 使用用户视角的过滤规则（不包含软删除 / 折叠 / REJECTED）
    """
    comment = comment_repo.get_comment_by_cid_for_user(cid)
    if not comment:
        raise CommentNotFound(message=f"comment {cid} not found")

    return comment.model_dump() if to_dict else comment

def get_comment_thread_for_user(
    comment_repo: ICommentRepository,
    cid: str,
    to_dict: bool = True,
) -> Dict | BatchCommentsOut:
    """
    查看某条评论所在整组对话（楼中楼完整线程）——用户视角：

    1. 先拿到这条评论（用户可见规则：过滤软删 / 折叠 / REJECTED）
    2. 根据它的 root_id 找到整组对话（同一个 root_id 的所有评论）
    3. 按仓库层返回的顺序（通常是 created_at ASC）返回 BatchCommentsOut
    """
    # 1. 先确认这条评论存在 & 用户可见
    current = comment_repo.get_comment_by_cid_for_user(cid)
    if not current:
        raise CommentNotFound(message=f"comment {cid} not found")

    # 2. 确定整组对话的 root_id
    root_id = current.root_id or current.cid

    # 3. 让仓库一次性查出整组对话（已经按时间排序）
    thread = comment_repo.list_comments_by_root_for_user(root_id=root_id)

    logger.info(
        f"[COMMENT] load thread for cid={cid}, root_id={root_id}, "
        f"total_in_thread={thread.total}, returned_count={thread.count}"
    )

    return thread.model_dump() if to_dict else thread

def get_comment_for_admin(
    comment_repo: ICommentRepository,
    cid: str,
    to_dict: bool = True,
) -> Dict | CommentAdminOut:
    """
    管理员：查看单条评论
    - 可见软删除 / 折叠 / REJECTED 等所有状态
    """
    comment = comment_repo.get_comment_by_cid_for_admin(cid)
    if not comment:
        raise CommentNotFound(message=f"comment {cid} not found")

    logger.info(f"[ADMIN] get comment cid={cid}")
    return comment.model_dump() if to_dict else comment


#------------------------------- 查询：楼中楼评论组 ------------------------------------

def get_comment_subtree_for_user(
    comment_repo: ICommentRepository,
    cid: str,
    to_dict: bool = True,
) -> Dict | BatchCommentsOut:
    """
    查看从某条评论开始的子树对话（只看这一支）——用户视角：

    1. 先拿到当前评论（用户可见规则）
    2. 用 root_id 查出整组对话（同一楼的所有评论）
    3. 在内存中根据 parent_id 构建树，从当前 cid 开始 DFS/BFS，拿到所有子孙
    4. 按原始时间顺序（即整组对话返回的顺序）返回结果
    """
    # 1. 拿到当前评论
    current = comment_repo.get_comment_by_cid_for_user(cid)
    if not current:
        raise CommentNotFound(message=f"comment {cid} not found")

    root_id = current.root_id or current.cid

    # 2. 拿到整组对话（同一 root_id 下的所有可见评论）
    thread = comment_repo.list_comments_by_root_for_user(root_id=root_id)
    all_comments: list[CommentOut] = thread.items

    if not all_comments:
        # 理论上不太可能（至少 current 在里面），防御性兜底
        raise CommentNotFound(message=f"no comments found under root_id={root_id}")

    # 3. 构建：cid -> CommentOut / parent_id -> [CommentOut] 的索引
    id_to_comment: dict[str, CommentOut] = {c.cid: c for c in all_comments}
    parent_to_children: dict[Optional[str], list[CommentOut]] = defaultdict(list)
    for c in all_comments:
        parent_to_children[c.parent_id].append(c)

    if cid not in id_to_comment:
        # 极端情况：当前评论在用户视角不可见（例如被折叠/删除），此时可以选择报错
        raise CommentNotFound(message=f"comment {cid} not visible for user (maybe deleted or hidden)")

    # 4. 从当前 cid 开始 DFS/BFS，收集整棵子树
    visited: set[str] = set()
    stack: list[str] = [cid]
    subtree_list: list[CommentOut] = []

    while stack:
        current_cid = stack.pop()
        if current_cid in visited:
            continue
        visited.add(current_cid)

        node = id_to_comment.get(current_cid)
        if not node:
            continue

        subtree_list.append(node)

        # 子节点压栈
        for child in parent_to_children.get(current_cid, []):
            stack.append(child.cid)

    # 5. 按“原始时间顺序”对 subtree 中的评论排序
    #    这里假设 all_comments 已经按 created_at 升序排好，
    #    我们用其索引位置还原顺序。
    position = {c.cid: idx for idx, c in enumerate(all_comments)}
    subtree_list.sort(key=lambda c: position.get(c.cid, 0))

    result = BatchCommentsOut(
        total=len(subtree_list),
        count=len(subtree_list),
        items=subtree_list,
    )

    logger.info(
        f"[COMMENT] load subtree for cid={cid}, root_id={root_id}, "
        f"subtree_size={result.count}"
    )

    return result.model_dump() if to_dict else result


#------------------------------- 查询：按帖子分页 ------------------------------------

def list_comments_by_post_for_user(
    comment_repo: ICommentRepository,
    post_id: str,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchCommentsOut:
    """
    普通用户 / 前台：查看某帖子的评论列表
    - 不包含软删除 / 折叠 / REJECTED 评论
    """
    result = comment_repo.list_comments_by_post_for_user(
        post_id=post_id,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result


def list_comments_by_post_for_reviewer(
    comment_repo: ICommentRepository,
    post_id: str,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchCommentsAdminOut:
    """
    审核员：查看某帖子的评论列表
    - 看得到所有审核状态（PENDING / APPROVED / REJECTED）
    - 不包含软删除
    """
    result = comment_repo.list_comments_by_post_for_reviewer(
        post_id=post_id,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result


def list_comments_by_post_for_admin(
    comment_repo: ICommentRepository,
    post_id: str,
    page: int = 0,
    page_size: int = 10,
    to_dict: bool = True,
) -> Dict | BatchCommentsAdminOut:
    """
    管理员：查看某帖子的评论列表
    - 含软删除、折叠、REJECTED 等所有状态
    """
    result = comment_repo.list_comments_by_post_for_admin(
        post_id=post_id,
        page=page,
        page_size=page_size,
    )
    return result.model_dump() if to_dict else result


#------------------------------- 更新：审核 & 状态 -----------------------------------

def review_comment(
    comment_repo: ICommentRepository,
    cid: str,
    data: ReviewUpdate,
    to_dict: bool = True,
) -> Dict | CommentAdminOut:
    """
    审核评论：
    1. 读取当前评论审核状态
    2. 校验状态流转是否合法（不允许从通过/拒绝回到待审）
    3. 更新审核状态 + 审核时间
    4. 返回 CommentAdminOut（方便审核页展示更多信息）
    """

    # 1. 获取当前评论（管理员视角：包含所有状态）
    current = comment_repo.get_comment_by_cid_for_admin(cid)
    if not current:
        raise CommentNotFound(message= f"comment {cid} not found")

    old_status = current.review_status
    new_status = data.review_status

    if new_status is None:
        # 没传新状态就不处理
        raise InvalidReviewStatusTransition("review_status cannot be None")

    # 2. 校验状态流转：
    #    不允许从 APPROVED / REJECTED 回到 PENDING
    if new_status == ReviewStatus.PENDING and old_status != ReviewStatus.PENDING:
        raise InvalidReviewStatusTransition(
            f"cannot change review_status from {old_status} back to PENDING"
        )

    # 3. 调用仓库更新审核状态 & 审核时间
    ok = comment_repo.update_review(cid, data)
    if not ok:
        # 极端情况：上一步还能查到，更新时却失败
        raise CommentNotFound(message= f"comment {cid} not found when updating review")

    # 4. 重新获取最新的评论信息返回
    updated = comment_repo.get_comment_by_cid_for_admin(cid)
    if not updated:
        raise CommentNotFound(message= f"comment {cid} not found after review update")

    logger.info(f"[REVIEW] updated comment cid={cid} review_status {old_status} -> {new_status}")
    return updated.model_dump() if to_dict else updated


def update_comment_status(
    comment_repo: ICommentRepository,
    cid: str,
    data: StatusUpdate,
    to_dict: bool = True,
) -> Dict | CommentAdminOut:
    """
    管理员更新评论显示状态（正常 / 折叠）：
    - 不涉及审核状态，只改 status
    """

    if data.status is None:
        raise InvalidReviewStatusTransition("status cannot be None")

    # 先确认评论存在
    current = comment_repo.get_comment_by_cid_for_admin(cid)
    if not current:
        raise CommentNotFound(message= f"comment {cid} not found")

    ok = comment_repo.update_status(cid, data)
    if not ok:
        raise CommentNotFound(message=f"comment {cid} not found when updating status")

    updated = comment_repo.get_comment_by_cid_for_admin(cid)
    if not updated:
        raise CommentNotFound(message=f"comment {cid} not found after status update")

    logger.info(f"[ADMIN] updated comment status cid={cid} -> {data.status}")
    return updated.model_dump() if to_dict else updated

#------------------------------- 删除：软删 & 硬删 -----------------------------------

def soft_delete_comment(
    comment_repo: ICommentRepository,
    stats_repo: IPostStatsRepository,  
    cid: str,
) -> bool:
    """
    普通用户软删除评论：
    - 实际上只是打上 deleted_at 时间戳
    - 是否只能删除自己的评论，通常由上层鉴权控制
    """
    data = comment_repo.get_comment_by_cid_for_admin(cid)
    ok = comment_repo.soft_delete_comment(cid)
    if ok:
        # 一级评论
        # （软）删除一级评论会将所有子评论都（软）删除
        if not data.parent_id and data.root_id == cid:
            stats_repo.update_comments(post_id=data.post_id, step=-data.comment_count)

        # 非一级评论：二级即更多级评论
        # （软）删除非一级评论，只（软）删除这一条评论
        
        # 二级评论
        if data.parent_id == data.root_id:
            stats_repo.update_comments(post_id=data.post_id, step=-1)
            comment_repo.update_comment_count(cid=data.parent_id, step=-1)
        # 三级或更多级评论
        if data.parent_id and data.parent_id != data.root_id:
            stats_repo.update_comments(post_id=data.post_id, step=-1)
            comment_repo.update_comment_count(cid=data.parent_id, step=-1)
            comment_repo.update_comment_count(cid=data.root_id, step=-1)
        
        logger.info(f"Soft deleted comment cid={cid}")
    else:
        logger.warning(f"Soft delete comment failed, cid={cid} not found")
    return ok

def restore_comment(
    comment_repo: ICommentRepository,
    stats_repo: IPostStatsRepository,
    cid: str,
) -> bool:
    """
    管理员恢复评论（撤销软删除）
    """
    data = comment_repo.get_comment_by_cid_for_admin(cid)
    ok = comment_repo.restore_comment(cid)
    if ok:
        # 一级评论
        # （软）删除一级评论会将所有子评论都（软）删除
        if not data.parent_id and data.root_id == cid:
            stats_repo.update_comments(post_id=data.post_id, step=data.comment_count)

        # 非一级评论：二级即更多级评论
        # （软）删除非一级评论，只（软）删除这一条评论
        
        # 二级评论
        if data.parent_id == data.root_id:
            stats_repo.update_comments(post_id=data.post_id, step=1)
            comment_repo.update_comment_count(cid=data.parent_id, step=1)
        # 三级或更多级评论
        if data.parent_id and data.parent_id != data.root_id:
            stats_repo.update_comments(post_id=data.post_id, step=1)
            comment_repo.update_comment_count(cid=data.parent_id, step=1)
            comment_repo.update_comment_count(cid=data.root_id, step=1)
        
        logger.info(f"[ADMIN] restored comment cid={cid}") 
    else:
        logger.warning(f"[ADMIN] restore comment failed, cid={cid} not found or not soft-deleted")

    return ok

def hard_delete_comment(
    comment_repo: ICommentRepository,
    cid: str,
) -> bool:
    """
    管理员硬删除评论：
    - 直接删除 comments 表记录
    - 通过 relationship(cascade='all, delete-orphan') 自动删除 CommentContent 等相关记录
    """
    data = comment_repo.get_comment_by_cid_for_admin(cid)
    if not data:
        raise CommentNotFound(message=f"comment {cid} not found")
    
    if data.deleted_at is None:
        raise CommentNotSoftDeletedError(message=f"comment {cid} must be soft-deleted before hard delete")
    
    ok = comment_repo.hard_delete_comment(cid)
    if ok:
        logger.info(f"[ADMIN] Hard deleted comment cid={cid}")
    else:
        logger.warning(f"[ADMIN] Hard delete failed, comment cid={cid} not found")
    return ok
