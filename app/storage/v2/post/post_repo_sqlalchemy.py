from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional
from app.models.v2.post import Post

from app.schemas.v2.post import PostOnlyCreate, PostOut, BatchPostsOut, PostDto
from app.schemas.v2.post_content import PostContentOut
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

    def _build_post_out(self, post: Post) -> PostOut:
        return PostOut(
            pid=post.pid,
            author_id=post.author_id,
            post_status=PostDto.model_validate(post),
            post_content=PostContentOut.model_validate(post.post_content) if post.post_content else None,
            post_stats=PostStatsDto.model_validate(post.post_stats) if post.post_stats else None,
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
        items = [self._build_post_out(p) for p in posts]
        return BatchPostsOut(total=total, count=len(items), items=items)

    def get_all(self, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        base_q = (
            self.db.query(Post)
            .options(joinedload(Post.post_content), joinedload(Post.post_stats))
            .filter(Post.deleted_at.is_(None))
        )
        total = base_q.count()
        posts = base_q.order_by(desc(Post._id)).offset(page * page_size).limit(page_size).all()
        items = [self._build_post_out(p) for p in posts]
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

    # 硬删除，删除 post 时会自动级联删除关联的 post_content 和 post_stats
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