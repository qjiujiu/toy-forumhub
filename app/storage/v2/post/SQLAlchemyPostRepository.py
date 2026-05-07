from datetime import timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional, List

from app.models.v2.post import Post
from app.models.v2.post_content import PostContent
from app.models.v2.post_stats import PostStats
from app.models.v2.user import User

from app.schemas.v2.post import (
    PostCreate,
    PostOnlyCreate,
    PostOut,
    BatchPostsOut,
    PostDto,
    TopPostOut,
    TopPostAuthorOut,
)
from app.schemas.v2.post_content import PostContentOut, PostContentUpdate
from app.schemas.v2.post_stats import PostStatsDto

from app.storage.v2.post.post_interface import IPostRepository

from app.core.time import now_utc8
from app.core.db import transaction


class SQLAlchemyPostRepository(IPostRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PostOnlyCreate) -> str:
        payload = data.model_dump(exclude_none=True)
        post = Post(**payload)

        with transaction(self.db):
            self.db.add(post)

        self.db.refresh(post)
        return post.pid

    def create_post(self, data: PostCreate) -> PostOut:
        """
        创建帖子聚合：一次事务内写入 posts + post_contents + post_stats。
        三张表要么都写成功，要么都失败回滚。
        """
        status = data.post_status or PostDto()
        post_payload = {"author_id": data.author_id}
        if status.visibility is not None:
            post_payload["visibility"] = status.visibility.value
        if status.publish_status is not None:
            post_payload["publish_status"] = status.publish_status.value

        post = Post(**post_payload)
        post_content = PostContent(post_id=post.pid, title=data.title, content=data.content)
        post_stats = PostStats(post_id=post.pid, like_count=0, comment_count=0)

        with transaction(self.db):
            self.db.add_all([post, post_content, post_stats])

        out = self.get_by_pid(post.pid)
        if not out:
            raise RuntimeError(f"post {post.pid} not found after creation")
        return out

    def _build_post_out(self, post: Post) -> Optional[PostOut]:
        """
        将 ORM Post 组装成 PostOut。
        - post_content 为必需字段：缺失则返回 None（视为数据不一致）。
        - post_stats 缺失时以 0/0 兜底。
        """
        if not post.post_content:
            return None

        stats_dto = PostStatsDto.model_validate(post.post_stats) if post.post_stats else PostStatsDto(like_count=0, comment_count=0)

        return PostOut(
            pid=post.pid,
            author_id=post.author_id,
            post_status=PostDto.model_validate(post),
            post_content=PostContentOut.model_validate(post.post_content),
            post_stats=stats_dto,
        )

    def get_by_pid(self, pid: str) -> Optional[PostOut]:
        post = (
            self.db.query(Post)
            .options(joinedload(Post.post_content), joinedload(Post.post_stats))
            .filter(Post.pid == pid)
            .filter(Post.deleted_at.is_(None))
            .first()
        )
        return self._build_post_out(post) if post else None

    def get_by_author(self, author_id: str, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        base_q = (
            self.db.query(Post)
            .options(joinedload(Post.post_content), joinedload(Post.post_stats))
            .filter(Post.author_id == author_id)
            .filter(Post.deleted_at.is_(None))
        )
        total = base_q.count()
        posts = base_q.order_by(desc(Post._id)).offset(page * page_size).limit(page_size).all()
        items = [out for p in posts if (out := self._build_post_out(p)) is not None]
        return BatchPostsOut(total=total, count=len(items), items=items)

    def get_all(self, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        base_q = (
            self.db.query(Post)
            .options(joinedload(Post.post_content), joinedload(Post.post_stats))
            .filter(Post.deleted_at.is_(None))
        )
        total = base_q.count()
        posts = base_q.order_by(desc(Post._id)).offset(page * page_size).limit(page_size).all()
        items = [out for p in posts if (out := self._build_post_out(p)) is not None]
        return BatchPostsOut(total=total, count=len(items), items=items)

    def update(self, pid: str, data: PostDto) -> bool:
        post = (
            self.db.query(Post)
            .filter(Post.pid == pid)
            .filter(Post.deleted_at.is_(None))
            .first()
        )
        if not post:
            return False
        update_data = data.model_dump(exclude_none=True)
        with transaction(self.db):
            for field, value in update_data.items():
                setattr(post, field, value)
        return True

    def update_content(self, pid: str, data: PostContentUpdate) -> bool:
        post_content = (
            self.db.query(PostContent)
            .filter(PostContent.post_id == pid)
            .first()
        )
        if not post_content:
            return False

        update_data = data.model_dump(exclude_none=True)
        with transaction(self.db):
            for field, value in update_data.items():
                setattr(post_content, field, value)
        return True

    def soft_delete(self, pid: str) -> bool:
        post = (
            self.db.query(Post)
            .filter(Post.pid == pid)
            .filter(Post.deleted_at.is_(None))
            .first()
        )
        if not post:
            return False
        with transaction(self.db):
            post.deleted_at = now_utc8()
        return True

    def hard_delete(self, pid: str) -> bool:
        post = (
            self.db.query(Post)
            .filter(Post.pid == pid)
            .first()
        )
        if not post:
            return False
        with transaction(self.db):
            self.db.delete(post)
        return True

    def get_top_liked_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        cutoff = now_utc8() - timedelta(days=7)
        rows = (
            self.db.query(PostStats, PostContent.title, User.uid, User.username, User.avatar_url)
            .join(PostContent, PostContent.post_id == PostStats.post_id)
            .join(Post, Post.pid == PostStats.post_id)
            .join(User, User.uid == Post.author_id)
            .filter(PostContent.created_at >= cutoff)
            .filter(Post.deleted_at.is_(None))
            .order_by(desc(PostStats.like_count), desc(PostStats._id))
            .limit(limit)
            .all()
        )

        items: List[TopPostOut] = []
        for stats, title, uid, username, avatar_url in rows:
            items.append(
                TopPostOut(
                    pid=stats.post_id,
                    title=title,
                    author=TopPostAuthorOut(uid=uid, username=username, avatar_url=avatar_url),
                    post_stats=PostStatsDto(like_count=stats.like_count, comment_count=stats.comment_count),
                )
            )
        return items

    def get_top_commented_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        cutoff = now_utc8() - timedelta(days=7)
        rows = (
            self.db.query(PostStats, PostContent.title, User.uid, User.username, User.avatar_url)
            .join(PostContent, PostContent.post_id == PostStats.post_id)
            .join(Post, Post.pid == PostStats.post_id)
            .join(User, User.uid == Post.author_id)
            .filter(PostContent.created_at >= cutoff)
            .filter(Post.deleted_at.is_(None))
            .order_by(desc(PostStats.comment_count), desc(PostStats._id))
            .limit(limit)
            .all()
        )

        items: List[TopPostOut] = []
        for stats, title, uid, username, avatar_url in rows:
            items.append(
                TopPostOut(
                    pid=stats.post_id,
                    title=title,
                    author=TopPostAuthorOut(uid=uid, username=username, avatar_url=avatar_url),
                    post_stats=PostStatsDto(like_count=stats.like_count, comment_count=stats.comment_count),
                )
            )
        return items
