# app/storage/comment/SQLAlchemyCommentRepository.py

from typing import Optional, List
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.comment import Comment, CommentStatus, ReviewStatus
from app.schemas.comment import (
    CommentOnlyCreate,
    CommentOut,
    CommentAdminOut,
    BatchCommentsOut,
    BatchCommentsAdminOut,
    ReviewUpdate,
    StatusUpdate,
)
from app.storage.comment.comment_interface import ICommentRepository
from app.core.db import transaction


# 统一一个东八区时间函数（如果你项目已有 now_utc8 可以直接用）
def now_utc8() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


class SQLAlchemyCommentRepository(ICommentRepository):
    """
    使用 SQLAlchemy 实现的评论仓库
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- 内部基础查询 ----------

    def _base_query(self):
        """最基础的查询：不做任何过滤（管理员用）"""
        return self.db.query(Comment)

    def _user_query(self):
        """
        普通用户可见的查询：
        - 不显示软删除
        - 不显示折叠评论
        - 不显示 REJECTED 的评论
        """
        return (
            self._base_query()
            .filter(
                Comment.deleted_at.is_(None),
                Comment.status == CommentStatus.NORMAL.value,
                Comment.review_status != ReviewStatus.REJECTED.value,
            )
        )

    def _reviewer_query(self):
        """
        审核员查询：
        - 看不到软删除
        - 可以看到所有 status / review_status
        """
        return self._base_query().filter(Comment.deleted_at.is_(None))

    def _admin_query(self):
        """
        管理员查询：
        - 不过滤软删除
        - 不过滤 status / review_status
        """
        return self._base_query()

    def _get_comment_orm(self, cid: str) -> Optional[Comment]:
        return (
            self.db.query(Comment)
            .filter(Comment.cid == cid)
            .first()
        )

    # ---------- 创建 ----------

    def create_comment(self, data: CommentOnlyCreate) -> str:
        """
        创建评论（仅 comments 表）：
        - root_id 可以由业务层填好，也可以先为空后续补
        """
        comment = Comment(
            post_id=data.post_id,
            author_id=data.author_id,
            parent_id=data.parent_id,
            root_id=data.root_id,
            status=data.status.value if data.status is not None else CommentStatus.NORMAL.value,
            review_status=(
                data.review_status.value
                if data.review_status is not None
                else ReviewStatus.PENDING.value
            ),
        )

        with transaction(self.db):
            self.db.add(comment)

        self.db.refresh(comment)
        
        # 一级评论规则： parent_id=None 且 root_id=None → root_id = cid
        if comment.parent_id is None and comment.root_id is None:
            comment.root_id = comment.cid
            with transaction(self.db):
                self.db.add(comment)

            self.db.refresh(comment)
        # 返回业务主键 cid
        return comment.cid

    # ---------- 单条查询 ----------

    def get_comment_by_cid_for_user(self, cid: str) -> Optional[CommentOut]:
        """
        普通用户 / 访客获取单条评论
        """
        comment: Optional[Comment] = (
            self._user_query()
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return None

        # 确认有内容记录
        if not comment.comment_content:
            raise RuntimeError(f"Comment(cid={cid}) missing content record")

        return CommentOut.model_validate(comment)

    def get_comment_by_cid_for_admin(self, cid: str) -> Optional[CommentAdminOut]:
        """
        管理员：获取单条评论（包含软删除 / 折叠 / REJECTED 等）
        """
        comment: Optional[Comment] = (
            self._admin_query()
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return None

        if not comment.comment_content:
            raise RuntimeError(f"Comment(cid={cid}) missing content record")

        # 这里 CommentAdminOut 里有 author: UserAllOut，
        # Pydantic 会根据 from_attributes 自动从 comment.author 映射
        return CommentAdminOut.model_validate(comment)

    # ---------- 按 root_id 查询列表 ----------
    def list_comments_by_root_for_user(self, root_id: str) -> BatchCommentsOut:
        """
        用户视角：根据 root_id 获取整组对话（楼）里的所有评论：
        - 过滤软删除 / 折叠 / REJECTED（由 _user_query 保证）
        - 只查指定 root_id
        - 按 created_at 升序返回（时间顺序）
        - 不分页，一次返回整组
        """
        rows: List[Comment] = (
            self._user_query()
            .filter(Comment.root_id == root_id)
            .order_by(Comment.created_at.asc())
            .all()
        )

        # 利用 Pydantic 的 from_attributes + 关系字段自动映射
        items = [CommentOut.model_validate(c) for c in rows]

        return BatchCommentsOut(
            total=len(items),
            count=len(items),
            items=items,
        )

    # ---------- 按帖子查询列表 ----------

    def list_comments_by_post_for_user(
        self,
        post_id: str,
        page: int,
        page_size: int,
    ) -> BatchCommentsOut:
        """
        普通用户 / 访客：查看某帖子的评论列表
        """
        base_q = (
            self._user_query()
            .filter(Comment.post_id == post_id,
                Comment.parent_id.is_(None),
                Comment.root_id == Comment.cid,
                )
            .order_by(Comment.created_at.asc())  
        )

        total = base_q.count()

        comments: List[Comment] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items: List[CommentOut] = []
        for c in comments:
            if not c.comment_content:
                # 开发阶段可以抛异常方便排查
                raise RuntimeError(f"Comment(cid={c.cid}) missing content record")

            items.append(CommentOut.model_validate(c))

        return BatchCommentsOut(
            total=total,
            count=len(items),
            items=items,
        )

    def list_comments_by_post_for_reviewer(
        self,
        post_id: str,
        page: int,
        page_size: int,
    ) -> BatchCommentsAdminOut:
        """
        审核员：查看某帖子的评论列表
        - 看得到所有审核状态
        - 不包含软删除
        """
        base_q = (
            self._reviewer_query()
            .filter(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
        )

        total = base_q.count()

        comments: List[Comment] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items: List[CommentAdminOut] = []
        for c in comments:
            if not c.comment_content:
                raise RuntimeError(f"Comment(cid={c.cid}) missing content record")

            items.append(CommentAdminOut.model_validate(c))

        return BatchCommentsAdminOut(
            total=total,
            count=len(items),
            items=items,
        )

    def list_comments_by_post_for_admin(
        self,
        post_id: str,
        page: int,
        page_size: int,
    ) -> BatchCommentsAdminOut:
        """
        管理员：查看某帖子的所有评论（含软删除）
        """
        base_q = (
            self._admin_query()
            .filter(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
        )

        total = base_q.count()

        comments: List[Comment] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items: List[CommentAdminOut] = []
        for c in comments:
            if not c.comment_content:
                # 管理员模式下也可以选择跳过异常数据：continue
                # 这里仍然抛异常方便你开发阶段发现问题
                raise RuntimeError(f"Comment(cid={c.cid}) missing content record")

            items.append(CommentAdminOut.model_validate(c))

        return BatchCommentsAdminOut(
            total=total,
            count=len(items),
            items=items,
        )

    # ---------- 审核 / 状态更新 ----------

    def update_review(self, cid: str, data: ReviewUpdate) -> bool:
        """
        更新评论审核状态：
        - 修改 review_status
        - 自动更新 reviewed_at
        """
        if data.review_status is None:
            # 没传就不用更新，直接返回 False 表示无操作
            return False

        comment: Optional[Comment] = (
            self._admin_query()  # 审核员 / 管理员都用此基础查询
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return False

        with transaction(self.db):
            comment.review_status = data.review_status.value
            comment.reviewed_at = now_utc8()

        return True

    def update_status(self, cid: str, data: StatusUpdate) -> bool:
        """
        更新评论状态（正常 / 折叠）：
        - 一般给管理员用
        """
        if data.status is None:
            return False

        comment: Optional[Comment] = (
            self._admin_query()
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return False

        with transaction(self.db):
            comment.status = data.status.value

        return True

    # ---------- 删除 ----------

    def soft_delete_comment(self, cid: str) -> bool:
        """
        软删除评论：
        - 设置 deleted_at 为当前时间
        """
        comment: Optional[Comment] = (
            self._admin_query()
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return False

        with transaction(self.db):
            comment.deleted_at = now_utc8()

        return True

    def restore_comment(self, cid: str) -> bool:
        """
        恢复软删除评论：
        - 将 deleted_at 置为 NULL
        - 注意：不恢复审核状态 / 折叠状态
        """
        # 管理员权限：可以看到软删除评论，因此用 _admin_query()
        comment: Optional[Comment] = (
            self._admin_query()
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return False

        if comment.deleted_at is None:
            # 已经是恢复状态，不需要重复处理
            return False

        with transaction(self.db):
            comment.deleted_at = None

        return True


    def hard_delete_comment(self, cid: str) -> bool:
        """
        硬删除评论：
        - 仅删除 Comment 记录
        - CommentContent 等建议通过 cascade 或业务层补充处理
        """
        comment: Optional[Comment] = (
            self._admin_query()
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return False

        with transaction(self.db):
            self.db.delete(comment)

        return True
    
    # ---------- 更新评论数与点赞数 ----------
    def update_comment_count(self, cid: str, step: int = 1) -> Optional[CommentOut]:
        """
        评论的子评论数自增/自减：
        - step 正数：+1
        - step 负数：-1（不会小于 0）
        """
        comment = self._get_comment_orm(cid)
        if comment is None:
            return None

        new_value = comment.comment_count + step
        comment.comment_count = max(new_value, 0)

        with transaction(self.db):
            pass

        self.db.refresh(comment)
        return CommentOut.model_validate(comment)
    
    def update_like_count(self, cid: str, step: int = 1) -> Optional[CommentOut]:
        """
        评论点赞数自增/自减：
        - step 正数：+1
        - step 负数：-1（不会小于 0）
        """
        comment = self._get_comment_orm(cid)
        if comment is None:
            return None

        new_value = comment.like_count + step
        comment.like_count = max(new_value, 0)

        with transaction(self.db):
            pass

        self.db.refresh(comment)
        return CommentOut.model_validate(comment)


