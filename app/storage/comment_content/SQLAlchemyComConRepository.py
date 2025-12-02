# app/storage/comment_content/SQLAlchemyCommentContentRepository.py

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.comment_content import CommentContent
from app.schemas.comment_content import (
    CommentContentCreate,
    CommentContentOut,
    BatchCommentContentsOut,
)
from app.storage.comment_content.comment_content_interface import (
    ICommentContentRepository,
)
from app.core.db import transaction


class SQLAlchemyCommentContentRepository(ICommentContentRepository):
    """
    使用 SQLAlchemy 实现的评论内容仓库
    业务层依赖 ICommentContentRepository 接口，而不是这个具体实现
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- 内部基础查询 ----------

    def _base_query(self):
        """内部基础查询：目前评论内容表没有软删除，直接全表查询"""
        return self.db.query(CommentContent)

    def get_by_ccid(self, ccid: str) -> Optional[CommentContentOut]:
        content = (
            self._base_query()
            .filter(CommentContent.ccid == ccid)
            .first()
        )
        return CommentContentOut.model_validate(content) if content else None

    def get_by_comment_id(self, comment_id: str) -> Optional[CommentContentOut]:
        content = (
            self._base_query()
            .filter(CommentContent.comment_id == comment_id)
            .first()
        )
        return CommentContentOut.model_validate(content) if content else None


    def list_by_comment_ids(self, comment_ids: List[str]) -> List[CommentContentOut]:
        if not comment_ids:
            return []

        contents: List[CommentContent] = (
            self._base_query()
            .filter(CommentContent.comment_id.in_(comment_ids))
            .all()
        )

        return [CommentContentOut.model_validate(c) for c in contents]

    def get_batch(self, page: int, page_size: int) -> BatchCommentContentsOut:
        """
        按 _id 倒序分页查询评论内容
        """
        base_q = self._base_query().order_by(CommentContent._id.desc())

        total = base_q.count()
        rows: List[CommentContent] = (
            base_q
            .offset(page * page_size)   # page 从 0 开始
            .limit(page_size)
            .all()
        )

        items = [CommentContentOut.model_validate(row) for row in rows]

        return BatchCommentContentsOut(
            total=total,
            count=len(items),
            items=items,
        )

    def create(self, data: CommentContentCreate) -> CommentContentOut:
        """
        创建评论内容：
        - comment_id 必须是已存在的 comments.cid（交由业务层或外键约束保证）
        """
        content = CommentContent(**data.model_dump())

        with transaction(self.db):
            self.db.add(content)

        self.db.refresh(content)
        return CommentContentOut.model_validate(content)

    def hard_delete_by_ccid(self, ccid: str) -> bool:
        """
        根据 ccid 物理删除评论内容
        """
        content = (
            self._base_query()
            .filter(CommentContent.ccid == ccid)
            .first()
        )
        if not content:
            return False

        with transaction(self.db):
            self.db.delete(content)

        return True

    def hard_delete_by_comment_id(self, comment_id: str) -> bool:
        """
        根据 comment_id 物理删除评论内容
        - 返回是否删除了至少一条记录
        """
        q = (
            self._base_query()
            .filter(CommentContent.comment_id == comment_id)
        )

        exists = q.first()
        if not exists:
            return False

        with transaction(self.db):
            # 批量删除
            q.delete(synchronize_session=False)

        return True
