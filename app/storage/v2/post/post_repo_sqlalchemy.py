from datetime import timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import Optional, List

from app.models.v2.post import Post
from app.models.v2.post_content import PostContent
from app.models.v2.post_stats import PostStats
from app.models.v2.user import User

from app.schemas.v2.post import PostOnlyCreate, PostCreate, PostOut, BatchPostsOut, PostDto, TopPostOut, TopPostAuthorOut
from app.schemas.v2.post_content import PostContentOut
from app.schemas.v2.post_content import PostContentUpdate
from app.schemas.v2.post_stats import PostStatsDto

from app.storage.v2.post.post_interface import IPostRepository

from app.core.time import now_utc8
from app.core.db import transaction


class SQLAlchemyPostRepository(IPostRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PostOnlyCreate) -> str:
        """
        v2 版本的 PostOnlyCreate 使用了 post_status(PostDto) 作为“状态聚合字段”。
        但 ORM 的 Post 表字段是 visibility/publish_status（两个 SMALLINT 列）。

        知识点：DTO/Schema 与 ORM Model 的差异
        - Schema/DTO 更适合表达“对外/对内”的语义（比如把几个字段打包成 post_status）
        - ORM Model 更贴近“存储结构”（列就是列）
        - 所以 repo 层通常需要做一次“字段映射”，把 Schema 转成 ORM 可写入的列。
        """
        status = data.post_status or PostDto()
        payload = {"author_id": data.author_id}

        # IntEnum 在 Python 里是 int 的子类：
        # - 数据库层最终存的是整数
        # - 这里显式取 .value 可以让读者更清楚“枚举值入库”的动作
        if status.visibility is not None:
            payload["visibility"] = status.visibility.value
        if status.publish_status is not None:
            payload["publish_status"] = status.publish_status.value

        post = Post(**payload)

        with transaction(self.db):
            self.db.add(post)

        self.db.refresh(post)
        return post.pid

    def create_post(self, data: PostCreate) -> PostOut:
        """
        创建帖子聚合：一次事务内写入 posts + post_contents + post_stats。
        为什么要在一个方法里完成？
        - 数据访问层的职责是隐藏多表细节, repo, 尽管物理存储上面, 已把帖子表拆成了三个数据表, 但是业务层仍然希望能把“帖子”当作一个整体；
        - 三张表要么都写成功，要么都失败回滚，这是典型的“聚合内一致性”。
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
            # add_all 会把三个对象都加入当前 session；事务提交时一起落库。
            self.db.add_all([post, post_content, post_stats])

        out = self.get_by_pid(post.pid)
        if not out:
            # 正常情况下不应发生；如果发生，说明出现了数据不一致或 get_by_pid 的聚合读取逻辑有 bug。
            raise RuntimeError(f"post {post.pid} not found after creation")
        return out

    def _build_post_out(self, post: Post) -> Optional[PostOut]:
        """
        将 ORM Post + 关系对象组装成对外 PostOut。

        注意：PostOut 的 post_content 在 schema 层是必填字段。
        - 如果数据库里出现“帖子行存在但 content 行缺失”，说明数据不完整。
        - 对这种异常数据，我们选择直接返回 None，让上层按“not found/数据不一致”处理。
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
        # 保护性处理：如果某些帖子缺少 content（数据不完整），这里选择跳过。
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
        """更新帖子内容（post_contents 表）。"""
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

    def get_top_liked_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        """返回近 7 天点赞数 TopN（帖子未软删除）。"""
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
        """返回近 7 天评论数 TopN（帖子未软删除）。"""
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
