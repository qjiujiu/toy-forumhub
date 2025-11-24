# app/storage/post_stats/SQLAlchemyPostStatsRepository.py

from typing import Optional
from sqlalchemy.orm import Session

from app.models.post_stats import PostStats
from app.schemas.post_stats import (
    PostStatsCreate,
    PostStatsUpdate,
    PostStatsOut,
    BatchPostStatsOut,
)
from app.storage.post_stats.post_stats_interface import IPostStatsRepository
from app.core.db import transaction


class SQLAlchemyPostStatsRepository(IPostStatsRepository):
    """
    使用 SQLAlchemy 实现的帖子统计仓库
    业务层依赖 IPostStatsRepository 抽象接口
    """

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        """内部基础查询（目前没有软删除字段，预留封装）"""
        return self.db.query(PostStats)

    def _get_stats_orm_by_post_id(self, post_id: str) -> Optional[PostStats]:
        return self._base_query().filter(PostStats.post_id == post_id).first()


    def get_by_psid(self, psid: str) -> Optional[PostStatsOut]:
        orm_obj = self._base_query().filter(PostStats.psid == psid).first()
        return PostStatsOut.model_validate(orm_obj) if orm_obj else None

    def get_by_post_id(self, post_id: str) -> Optional[PostStatsOut]:
        orm_obj = self._get_stats_orm_by_post_id(post_id)
        return PostStatsOut.model_validate(orm_obj) if orm_obj else None

    def get_batch(self, page: int, page_size: int) -> BatchPostStatsOut:
        """
        简单分页查询帖子统计信息
        """
        base_q = self._base_query().order_by(PostStats._id.desc())

        total = base_q.count()
        rows = (
            base_q
            .offset(page * page_size)   # page 从 0 开始
            .limit(page_size)
            .all()
        )

        items = [PostStatsOut.model_validate(row) for row in rows]

        return BatchPostStatsOut(
            total=total,
            count=len(items),
            items=items,
        )


    def create(self, data: PostStatsCreate) -> PostStatsOut:
        """
        直接按传入数据创建统计记录
        """
        payload = data.model_dump(exclude_none=True)
        orm_obj = PostStats(**payload)

        with transaction(self.db):
            self.db.add(orm_obj)

        self.db.refresh(orm_obj)
        return PostStatsOut.model_validate(orm_obj)

    def create_for_post(self, post_id: str) -> PostStatsOut:
        """
        为某个帖子初始化统计记录：
        - 如果已存在，则直接返回
        - 如果不存在，则新建 like_count=0, comment_count=0
        """
        stats = self._get_stats_orm_by_post_id(post_id)
        if stats is None:
            stats = PostStats(
                post_id=post_id,
                like_count=0,
                comment_count=0,
            )
            with transaction(self.db):
                self.db.add(stats)
            self.db.refresh(stats)

        return PostStatsOut.model_validate(stats)


    def update_stats(self, post_id: str, data: PostStatsUpdate) -> Optional[PostStatsOut]:
        """
        根据 post_id 更新统计数据（整体更新）
        """
        stats = self._get_stats_orm_by_post_id(post_id)
        if stats is None:
            return None

        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            # 没有任何需要更新的字段
            return PostStatsOut.model_validate(stats)

        with transaction(self.db):
            for field, value in update_data.items():
                setattr(stats, field, value)

        self.db.refresh(stats)
        return PostStatsOut.model_validate(stats)

    def update_likes(self, post_id: str, step: int = 1) -> PostStatsOut:
        """
        点赞数自增/自减，限制不小于 0
        """
        stats = self._get_stats_orm_by_post_id(post_id)
        if stats is None:
            # 如果希望在第一次点赞时自动创建统计记录，可以：
            stats = PostStats(
                post_id=post_id,
                like_count=0,
                comment_count=0,
            )
            with transaction(self.db):
                self.db.add(stats)
            self.db.refresh(stats)

        new_value = stats.like_count + step
        stats.like_count = max(new_value, 0)

        with transaction(self.db):
            # 已在 stats 上修改，transaction 结束时会 flush/commit
            pass

        self.db.refresh(stats)
        return PostStatsOut.model_validate(stats)

    def update_comments(self, post_id: str, step: int = 1) -> PostStatsOut:
        """
        评论数自增/自减，限制不小于 0
        """
        stats = self._get_stats_orm_by_post_id(post_id)
        if stats is None:
            stats = PostStats(
                post_id=post_id,
                like_count=0,
                comment_count=0,
            )
            with transaction(self.db):
                self.db.add(stats)
            self.db.refresh(stats)

        new_value = stats.comment_count + step
        stats.comment_count = max(new_value, 0)

        with transaction(self.db):
            pass

        self.db.refresh(stats)
        return PostStatsOut.model_validate(stats)


    def delete_by_post_id(self, post_id: str) -> bool:
        """
        硬删除指定 post 对应的统计记录
        """
        stats = self._get_stats_orm_by_post_id(post_id)
        if stats is None:
            return False

        with transaction(self.db):
            self.db.delete(stats)

        return True
