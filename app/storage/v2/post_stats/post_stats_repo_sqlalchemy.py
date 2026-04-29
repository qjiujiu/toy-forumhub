from datetime import timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional, List
from app.models.v1.post_stats import PostStats
from app.models.v1.post_content import PostContent
from app.models.v1.post import Post

from app.schemas.v2.post_stats import PostStatsCreate, PostStatsOut, PostStatsDto, BatchPostStatsOut
from app.schemas.v2.post import TopPostOut, TopPostAuthorOut

from app.storage.v2.post_stats.post_stats_interface import IPostStatsRepository

from app.core.time import now_utc8
from app.core.db import transaction


class SQLAlchemyPostStatsRepository(IPostStatsRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PostStatsCreate) -> str:
        post_stats = PostStats(
            post_id=data.post_id,
            like_count=data.post_stats.like_count or 0,
            comment_count=data.post_stats.comment_count or 0,
        )
        with transaction(self.db):
            self.db.add(post_stats)
        self.db.refresh(post_stats)
        return post_stats.psid

    def get_by_post_id(self, post_id: str) -> Optional[PostStatsOut]:
        post_stats = (
            self.db.query(PostStats)
            .filter(PostStats.post_id == post_id)
            .first()
        )
        return PostStatsOut.model_validate(post_stats) if post_stats else None

    def update(self, post_id: str, data: PostStatsDto, delta: int = 1) -> bool:
        post_stats = (
            self.db.query(PostStats)
            .filter(PostStats.post_id == post_id)
            .first()
        )
        if not post_stats:
            return False
        update_data = data.model_dump(exclude_none=True)
        with transaction(self.db):
            for field, value in update_data.items():
                setattr(post_stats, field, getattr(post_stats, field) + delta)
        return True

    def get_top_liked(self, limit: int = 10) -> BatchPostStatsOut:
        cutoff = now_utc8() - timedelta(days=7)
        rows = (
            self.db.query(PostStats)
            .join(PostContent, PostContent.post_id == PostStats.post_id)
            .filter(PostContent.created_at >= cutoff)
            .order_by(desc(PostStats.like_count), desc(PostStats._id))
            .limit(limit)
            .all()
        )
        items = [PostStatsOut.model_validate(r) for r in rows]
        return BatchPostStatsOut(total=len(items), count=len(items), items=items)

    def get_top_commented(self, limit: int = 10) -> BatchPostStatsOut:
        cutoff = now_utc8() - timedelta(days=7)
        rows = (
            self.db.query(PostStats)
            .join(PostContent, PostContent.post_id == PostStats.post_id)
            .filter(PostContent.created_at >= cutoff)
            .order_by(desc(PostStats.comment_count), desc(PostStats._id))
            .limit(limit)
            .all()
        )
        items = [PostStatsOut.model_validate(r) for r in rows]
        return BatchPostStatsOut(total=len(items), count=len(items), items=items)

    def get_top_liked_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        from app.models.v1.user import User
        cutoff = now_utc8() - timedelta(days=7)
        rows = (
            self.db.query(PostStats)
            .join(PostContent, PostContent.post_id == PostStats.post_id)
            .join(Post, Post.pid == PostStats.post_id)
            .join(User, User.uid == Post.author_id)
            .filter(PostContent.created_at >= cutoff)
            .filter(Post.deleted_at.is_(None))
            .order_by(desc(PostStats.like_count), desc(PostStats._id))
            .limit(limit)
            .all()
        )
        items = []
        for r in rows:
            post_content = self.db.query(PostContent).filter(PostContent.post_id == r.post_id).first()
            post = self.db.query(Post).filter(Post.pid == r.post_id).first()
            user = self.db.query(User).filter(User.uid == post.author_id).first() if post else None
            items.append(TopPostOut(
                pid=r.post_id,
                title=post_content.title if post_content else "",
                author=TopPostAuthorOut(
                    uid=user.uid if user else "",
                    username=user.username if user else "",
                    avatar_url=user.avatar_url if user else None,
                ),
                post_stats=PostStatsDto(
                    like_count=r.like_count,
                    comment_count=r.comment_count,
                ),
            ))
        return items

    def get_top_commented_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        from app.models.v1.user import User
        cutoff = now_utc8() - timedelta(days=7)
        rows = (
            self.db.query(PostStats)
            .join(PostContent, PostContent.post_id == PostStats.post_id)
            .join(Post, Post.pid == PostStats.post_id)
            .join(User, User.uid == Post.author_id)
            .filter(PostContent.created_at >= cutoff)
            .filter(Post.deleted_at.is_(None))
            .order_by(desc(PostStats.comment_count), desc(PostStats._id))
            .limit(limit)
            .all()
        )
        items = []
        for r in rows:
            post_content = self.db.query(PostContent).filter(PostContent.post_id == r.post_id).first()
            post = self.db.query(Post).filter(Post.pid == r.post_id).first()
            user = self.db.query(User).filter(User.uid == post.author_id).first() if post else None
            items.append(TopPostOut(
                pid=r.post_id,
                title=post_content.title if post_content else "",
                author=TopPostAuthorOut(
                    uid=user.uid if user else "",
                    username=user.username if user else "",
                    avatar_url=user.avatar_url if user else None,
                ),
                post_stats=PostStatsDto(
                    like_count=r.like_count,
                    comment_count=r.comment_count,
                ),
            ))
        return items