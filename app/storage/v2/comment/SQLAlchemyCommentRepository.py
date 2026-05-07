from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.comment import Comment, CommentStatus, ReviewStatus
from app.models.comment_content import CommentContent

from app.schemas.v2.comment import (
    CommentCreate,
    CommentOnlyCreate,
    CommentOut,
    BatchCommentsOut,
    StatusUpdate,
    CommentQueryDTO,
    CommentUpdate,
)
from app.schemas.v2.comment_content import CommentContentCreate

from app.storage.v2.comment.comment_interface import ICommentRepository

from app.core.time import now_utc8
from app.core.db import transaction


class SQLAlchemyCommentRepository(ICommentRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CommentOnlyCreate) -> str:
        comment = Comment(
            post_id=data.post_id,
            author_id=data.author_id,
            like_count=data.like_count,
            comment_count=data.comment_count,
            status=data.status,
            review_status=data.review_status,
            parent_id=data.parent_id,
            root_id=data.root_id,
        )
        with transaction(self.db):
            self.db.add(comment)
        self.db.refresh(comment)
        return comment.cid

    def create_comment(self, data: CommentCreate) -> CommentOut:
        """
        创建评论聚合：一次事务内写入 comments + comment_contents。
        """
        root_id = data.root_id or ""

        comment = Comment(
            post_id=data.post_id,
            author_id=data.author_id,
            like_count=0,
            comment_count=0,
            parent_id=data.parent_id,
            root_id=root_id,
        )

        with transaction(self.db):
            self.db.add(comment)
            self.db.flush()  # 获取 comment.cid

            # 如果 root_id 为空（首层评论），更新为自身 cid
            if data.root_id is None:
                comment.root_id = comment.cid

            content = CommentContent(
                comment_id=comment.cid,
                content=data.content,
            )
            self.db.add(content)

        self.db.refresh(comment)
        return CommentOut.model_validate(comment)

    def _build_comment_out(self, comment: Comment) -> Optional[CommentOut]:
        if not comment.comment_content:
            return None
        return CommentOut.model_validate(comment)

    def get_by_cid(self, cid: str) -> Optional[CommentOut]:
        comment = (
            self.db.query(Comment)
            .options(joinedload(Comment.comment_content))
            .filter(Comment.cid == cid)
            .filter(Comment.deleted_at.is_(None))
            .first()
        )
        return self._build_comment_out(comment) if comment else None

    def get_comments(
        self,
        query: CommentQueryDTO,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchCommentsOut:
        base_q = (
            self.db.query(Comment)
            .options(joinedload(Comment.comment_content))
            .filter(Comment.deleted_at.is_(None))
        )

        for field_name in query.model_fields:
            field_value = getattr(query, field_name, None)
            if field_value is not None:
                model_field = getattr(Comment, field_name, None)
                if model_field is not None:
                    base_q = base_q.filter(model_field == field_value)

        base_q = base_q.order_by(desc(Comment._id))

        total = base_q.count()
        comments_orm = base_q.offset(page * page_size).limit(page_size).all()
        comments_out = [out for c in comments_orm if (out := self._build_comment_out(c)) is not None]

        return BatchCommentsOut(
            total=total,
            count=len(comments_out),
            items=comments_out,
        )

    def update(self, cid: str, data: StatusUpdate) -> bool:
        comment = (
            self.db.query(Comment)
            .filter(Comment.cid == cid)
            .filter(Comment.deleted_at.is_(None))
            .first()
        )
        if not comment:
            return False

        update_data = data.model_dump(exclude_none=True)
        with transaction(self.db):
            for field, value in update_data.items():
                setattr(comment, field, value)
        return True

    def update_counters(self, cid: str, data: CommentUpdate) -> bool:
        comment = (
            self.db.query(Comment)
            .filter(Comment.cid == cid)
            .filter(Comment.deleted_at.is_(None))
            .first()
        )
        if not comment:
            return False

        update_data = data.model_dump(exclude_none=True)
        with transaction(self.db):
            for field, delta in update_data.items():
                if delta:
                    current = getattr(comment, field)
                    setattr(comment, field, max(0, current + delta) )
        return True

    def hard_delete(self, cid: str) -> bool:
        comment = (
            self.db.query(Comment)
            .filter(Comment.cid == cid)
            .first()
        )
        if not comment:
            return False
        with transaction(self.db):
            self.db.delete(comment)
        return True

    def soft_delete(self, cid: str) -> bool:
        comment = (
            self.db.query(Comment)
            .filter(Comment.cid == cid)
            .filter(Comment.deleted_at.is_(None))
            .first()
        )
        if not comment:
            return False
        with transaction(self.db):
            comment.deleted_at = now_utc8()
        return True
