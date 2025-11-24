# app/storage/post_content/SQLAlchemyPostContentRepository.py

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.post_content import PostContent
from app.schemas.post_content import (
    PostContentCreate,
    PostContentUpdate,
    PostContentOut,
    BatchPostContentsOut,
)
from app.storage.post_content.post_content_interface import IPostContentRepository
from app.core.db import transaction


class SQLAlchemyPostContentRepository(IPostContentRepository):
    """
    使用 SQLAlchemy 实现的帖子内容仓库
    业务层依赖 IPostContentRepository 抽象接口
    """

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        """内部基础查询入口（目前没有软删除字段，预留封装）"""
        return self.db.query(PostContent)

    def get_by_pcid(self, pcid: str) -> Optional[PostContentOut]:
        orm_obj = self._base_query().filter(PostContent.pcid == pcid).first()
        return PostContentOut.model_validate(orm_obj) if orm_obj else None

    def get_by_post_id(self, post_id: str) -> Optional[PostContentOut]:
        """
        post_id 在表上是 UNIQUE，因此只会取到 0 或 1 条
        """
        orm_obj = self._base_query().filter(PostContent.post_id == post_id).first()
        return PostContentOut.model_validate(orm_obj) if orm_obj else None

    # 可能用不上
    def get_batch(self, page: int, page_size: int) -> BatchPostContentsOut:
        """
        简单的分页查询帖子内容
        - 按 _id 倒序（你可以根据需要换成其他 order_by）
        """
        base_q = self._base_query().order_by(PostContent._id.desc())

        total = base_q.count()
        rows = (
            base_q
            .offset(page * page_size)   # page 从 0 开始
            .limit(page_size)
            .all()
        )

        items = [PostContentOut.model_validate(row) for row in rows]

        return BatchPostContentsOut(
            total=total,
            count=len(items),
            items=items,
        )

    def create(self, data: PostContentCreate) -> PostContentOut:
        """
        创建帖子内容
        """
        payload = data.model_dump(exclude_none=True)
        orm_obj = PostContent(**payload)

        with transaction(self.db):
            self.db.add(orm_obj)

        self.db.refresh(orm_obj)
        return PostContentOut.model_validate(orm_obj)

    def update_by_pcid(self, pcid: str, data: PostContentUpdate) -> Optional[PostContentOut]:
        """
        根据 pcid 更新帖子内容
        """
        orm_obj = self._base_query().filter(PostContent.pcid == pcid).first()
        if not orm_obj:
            return None

        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            # 没有任何需要更新的字段，直接返回当前结果
            return PostContentOut.model_validate(orm_obj)

        with transaction(self.db):
            for field, value in update_data.items():
                setattr(orm_obj, field, value)

        self.db.refresh(orm_obj)
        return PostContentOut.model_validate(orm_obj)

    def delete_by_pcid(self, pcid: str) -> bool:
        """
        硬删除帖子内容
        - 可以在业务层控制：只允许管理员/作者删除
        """
        orm_obj = self._base_query().filter(PostContent.pcid == pcid).first()
        if not orm_obj:
            return False

        with transaction(self.db):
            self.db.delete(orm_obj)

        return True
