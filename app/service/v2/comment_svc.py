from typing import Dict, List, Optional, Union

from app.schemas.v2.comment import (
    CommentCreate, CommentOnlyCreate, CommentOut,
    BatchCommentsOut, CommentQueryDTO, StatusUpdate, CommentUpdate,
)
from app.schemas.v2.post import PostOut
from app.schemas.v2.post_stats import PostStatsDto

from app.storage.v2.comment.comment_interface import ICommentRepository
from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.user.user_interface import IUserRepository

from app.schemas.v2.user import UserRole, UserStatus
from app.models.v2.comment import CommentStatus, ReviewStatus

import logging
logger = logging.getLogger(__name__)
from app.kit.exceptions import CommentNotFound, UserNotFound, AdminPermissionDenied, ForbiddenAction, CommentNotSoftDeletedError


class CommentService:

    def __init__(
        self,
        comment_repo: ICommentRepository,
        post_repo: IPostRepository,
        user_repo: IUserRepository,
    ):
        self._comment_repo = comment_repo
        self._post_repo = post_repo
        self._user_repo = user_repo

    def _verify_admin(self, uid: str) -> None:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(user_id=uid)
        if user.user_info.role != UserRole.ADMIN:
            raise AdminPermissionDenied(f"user {uid} is not an admin")

    def _verify_user_active(self, uid: str) -> None:
        """校验用户存在且状态正常，封禁/冻结用户禁止操作。"""
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(user_id=uid)
        if user.user_info.status != UserStatus.NORMAL:
            raise ForbiddenAction(f"user {uid} is not active (status={user.user_info.status})")

    # ==================== C ====================

    def create_comment(self, data: CommentCreate, to_dict: bool = True) -> Union[Dict, str]:
        """创建评论并更新计数（帖子 + 父评论层级）。"""
        post = self._post_repo.get_by_pid(data.post_id)
        if not post:
            raise ValueError(f"post {data.post_id} not found")

        self._verify_user_active(data.author_id)

        comment_out = self._comment_repo.create_comment(data)

        # 1. 帖子 comment_count +1
        self._post_repo.update_stats(data.post_id, PostStatsDto(comment_count=1))

        # 2. 如果是一级以下评论，更新父级 comment_count
        if data.parent_id is not None:
            # 二级：parent_id == root_id
            if data.parent_id == data.root_id or data.parent_id == comment_out.root_id:
                self._comment_repo.update_counters(data.parent_id, CommentUpdate(comment_count=1))
            else:
                # 三级及以上：父节点 + 根节点
                self._comment_repo.update_counters(data.parent_id, CommentUpdate(comment_count=1))
                self._comment_repo.update_counters(comment_out.root_id, CommentUpdate(comment_count=1))

        logger.info(f"[CREATE_COMMENT] Created comment cid={comment_out.cid} for post={data.post_id}")

        if to_dict:
            return comment_out.model_dump()
        return comment_out.cid

    # ==================== R ====================

    def get_comment(self, cid: str) -> Optional[CommentOut]:
        return self._comment_repo.get_by_cid(cid)

    def get_comments_by_post_id(
        self, post_id: str, page: int = 0, page_size: int = 20,
    ) -> BatchCommentsOut:
        """按帖子 ID 获取评论列表。"""
        return self._comment_repo.get_comments(
            CommentQueryDTO(post_id=post_id), page, page_size,
        )

    def get_comments_by_author_id(
        self, author_id: str, page: int = 0, page_size: int = 20,
    ) -> BatchCommentsOut:
        """按作者 ID 获取评论列表。"""
        return self._comment_repo.get_comments(
            CommentQueryDTO(author_id=author_id), page, page_size,
        )

    def get_comments_by_root_id(
        self, root_id: str, page: int = 0, page_size: int = 20,
    ) -> BatchCommentsOut:
        """按根评论 ID 获取楼中楼完整线程。"""
        return self._comment_repo.get_comments(
            CommentQueryDTO(root_id=root_id), page, page_size,
        )

    def get_comments_by_parent_id(
        self, parent_id: Optional[str], page: int = 0, page_size: int = 20,
    ) -> BatchCommentsOut:
        """
        按父评论 ID 获取子评论。
        - parent_id=None → 查询一级评论（顶级评论）
        - parent_id=具体值 → 查询某父评论的直接子回复
        """
        return self._comment_repo.get_comments(
            CommentQueryDTO(parent_id=parent_id), page, page_size,
        )

    def get_top_comments_by_post(
        self, post_id: str, page: int = 0, page_size: int = 20,
    ) -> BatchCommentsOut:
        """获取某帖子下的一级评论（parent_id IS NULL）。"""
        return self._comment_repo.get_comments(
            CommentQueryDTO(post_id=post_id, parent_id=None), page, page_size,
        )

    # ==================== U ====================

    def ban_comment(self, admin_uid: str, cid: str) -> bool:
        """封禁评论：将 review_status 设为 REJECTED（审核拒绝），评论将不再展示。"""
        self._verify_admin(admin_uid)
        return self._comment_repo.update(cid, StatusUpdate(review_status=ReviewStatus.REJECTED))

    def unban_comment(self, admin_uid: str, cid: str) -> bool:
        """解封评论：将 review_status 设为 APPROVED（审核通过），评论恢复正常展示。"""
        self._verify_admin(admin_uid)
        return self._comment_repo.update(cid, StatusUpdate(review_status=ReviewStatus.APPROVED))

    def fold_comment(self, admin_uid: str, cid: str) -> bool:
        """折叠评论：将 status 设为 FOLDED（折叠），评论被折叠隐藏。"""
        self._verify_admin(admin_uid)
        return self._comment_repo.update(cid, StatusUpdate(status=CommentStatus.FOLDED))

    # ==================== D ====================
    #  TODO：管理员也应有权限软删除评论
    def delete_comment(self, uid: str, cid: str) -> bool:
        """
        软删除评论并更新所有相关计数。

        子评论不直接展示在帖子列表下（需要通过一级评论展开），
        因此一级评论软删除时无需级联删除子孙，仅将自身 deleted_at 置为当前时间即可。

        分级递减规则：
        - 一级（parent_id IS NULL）: 帖子 -= (comment_count + 1)
        - 二级（parent_id == root_id）: 帖子 -= 1，根节点 -= 1
        - 三级+（parent_id != root_id）: 帖子 -= 1，父节点 -= 1，根节点 -= 1
        """
        self._verify_user_active(uid)
        comment = self._comment_repo.get_by_cid(cid)
        if not comment:
            raise CommentNotFound(cid=cid)
        if comment.author_id != uid:
            raise ForbiddenAction(f"user {uid} is not the author of comment {cid}")

        is_level1 = comment.parent_id is None

        if is_level1:
            # 一级：只删自身，子孙靠 root 不可见自然消失
            # TODO：后续考虑联级软删除（即同时更新子孙 deleted_at）
            self._comment_repo.soft_delete(cid)
            self._post_repo.update_stats(comment.post_id, PostStatsDto(comment_count=-(comment.comment_count + 1)))
        else:
            # 二级 / 三级+
            self._comment_repo.soft_delete(cid)
            self._post_repo.update_stats(comment.post_id, PostStatsDto(comment_count=-1))

            if comment.parent_id == comment.root_id:
                # 二级：根节点减一
                self._comment_repo.update_counters(comment.root_id, CommentUpdate(comment_count=-1))
            else:
                # 三级+：父节点和根节点都减一
                self._comment_repo.update_counters(comment.parent_id, CommentUpdate(comment_count=-1))
                self._comment_repo.update_counters(comment.root_id, CommentUpdate(comment_count=-1))

        logger.info(f"[DELETE_COMMENT] Soft deleted comment cid={cid}")
        return True

    def hard_delete_comment(self, admin_uid: str, cid: str) -> bool:
        """
        硬删除评论（仅允许对已软删除的评论执行硬删除）。

        前置条件：
        - 调用者必须是管理员
        - 评论必须已软删除（deleted_at IS NOT NULL）

        硬删除后不再更新计数，因为软删除时已经更新过。
        """
        self._verify_admin(admin_uid)

        # 如果 get_by_cid 能查到，说明未被软删除 → 不允许硬删除
        comment = self._comment_repo.get_by_cid(cid)
        if comment:
            raise CommentNotSoftDeletedError(f"comment {cid} is not soft-deleted, cannot hard delete")

        # 执行硬删除（仅删除已软删除的记录）
        ok = self._comment_repo.hard_delete(cid)
        if not ok:
            raise CommentNotFound(f"comment {cid} not found")

        logger.info(f"[HARD_DELETE_COMMENT] Hard deleted comment cid={cid} by admin={admin_uid}")
        return True

    def get_post_by_comment_cid(self, cid: str, to_dict: bool = True) -> Union[Dict, PostOut]:
        comment = self._comment_repo.get_by_cid(cid)
        if not comment:
            raise CommentNotFound(f"comment {cid} not found")
        post = self._post_repo.get_by_pid(comment.post_id)
        return post.model_dump() if to_dict and post else post
