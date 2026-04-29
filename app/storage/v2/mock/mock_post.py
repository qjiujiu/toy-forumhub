import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from app.models.v2.post import PostPublishStatus, PostVisibility
from app.schemas.v2.post import (
    BatchPostsOut,
    PostCreate,
    PostDto,
    PostOnlyCreate,
    PostOut,
    TopPostAuthorOut,
    TopPostOut,
)
from app.schemas.v2.post_content import PostContentOut, PostContentUpdate
from app.schemas.v2.post_stats import PostStatsDto


_TZ_UTC8 = timezone(timedelta(hours=8))


class MockPostRepository:
    """v2 内存版 Post 聚合仓储（Aggregate Repository）。

    设计目标：与 `app/storage/v2/post/post_interface.py` 的协议保持一致。

    关键教学点：
    - 数据库里虽然拆成 `posts/post_contents/post_stats` 三表，但是 repo 对外仍是“一个对象”。
    - mock repo 不再用使用三个 repo 互相组装, 而是在一个对象里维护 3 份内存数据，模拟三表。
    """

    def __init__(self, user_repo=None):
        # posts[pid] = {"_id": int, "pid": str, "author_id": str, "post_status": PostDto, "deleted_at": datetime|None}
        self.posts: Dict[str, dict] = {}

        # contents[pid] = PostContentOut（模拟 post_contents 表）
        self.contents: Dict[str, PostContentOut] = {}

        # stats[pid] = PostStatsDto（模拟 post_stats 表）
        self.stats: Dict[str, PostStatsDto] = {}

        # 用自增整数模拟 posts._id（用于排序/稳定性）
        self._auto_id = 0

        # 为热榜输出作者信息（SQLAlchemy repo 会 join user 表；mock 用 repo 注入来模拟）
        self._user_repo = user_repo

    def _now(self) -> datetime:
        return datetime.now(_TZ_UTC8)

    def _normalize_status(self, status: Optional[PostDto]) -> PostDto:
        """把“未显式传入”的字段补成与数据库一致的默认值。

        说明：
        - SQLAlchemy 模型里 `visibility/publish_status` 都有默认值；repo 层如果不显式写入，会落到 DB default。
        - mock 没有 DB，所以需要在内存里补默认值，否则 service 的状态机逻辑会出现偏差。
        """

        s = status or PostDto()
        if s.visibility is None:
            s.visibility = PostVisibility.PUBLIC
        if s.publish_status is None:
            s.publish_status = PostPublishStatus.PUBLISHED
        return s

    # ========== 增 ==========

    def create(self, data: PostOnlyCreate) -> str:
        """只写入 posts 这张“状态/索引表”（mock 版）。"""

        self._auto_id += 1
        pid = str(uuid.uuid4())
        status = self._normalize_status(data.post_status)
        self.posts[pid] = {
            "_id": self._auto_id,
            "pid": pid,
            "author_id": data.author_id,
            "post_status": status,
            "deleted_at": None,
        }
        return pid

    def create_post(self, data: PostCreate) -> PostOut:
        """创建帖子聚合：一次性写入 posts + post_contents + post_stats（mock 版）。"""

        pid = self.create(PostOnlyCreate(author_id=data.author_id, post_status=data.post_status))

        # mock 版的“同一事务”体现为：在一个函数里把三份数据同时写入。
        # 如果未来要模拟失败回滚，可以在这里引入 try/except 并回滚内存字典。
        now = self._now()
        self.contents[pid] = PostContentOut(
            pcid=str(uuid.uuid4()),
            post_id=pid,
            title=data.title,
            content=data.content,
            created_at=now,
        )
        self.stats[pid] = PostStatsDto(like_count=0, comment_count=0)

        out = self.get_by_pid(pid)
        if not out:
            # 正常情况下不应发生；如果发生说明 mock 的聚合读取逻辑写坏了。
            raise RuntimeError(f"post {pid} not found after creation")
        return out

    # ========== 查 ==========

    def _build_post_out(self, post_row: dict) -> Optional[PostOut]:
        """把三份内存数据组装成 `PostOut`。

        教学点：
        - `PostOut.post_content` 在 schema 层是必填。
        - 如果出现 posts 存在但 content 缺失，说明“聚合不变式”被破坏。
          我们选择返回 None，让上层尽早暴露问题（fail fast）。
        """

        pid = post_row["pid"]
        content = self.contents.get(pid)
        if not content:
            return None

        stats = self.stats.get(pid) or PostStatsDto(like_count=0, comment_count=0)
        return PostOut(
            pid=pid,
            author_id=post_row["author_id"],
            post_status=post_row["post_status"],
            post_content=content,
            post_stats=stats,
        )

    def get_by_pid(self, pid: str) -> Optional[PostOut]:
        post = self.posts.get(pid)
        if not post:
            return None
        if post.get("deleted_at") is not None:
            return None
        return self._build_post_out(post)

    def get_by_author(self, author_id: str, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        rows = [p for p in self.posts.values() if p["author_id"] == author_id and p.get("deleted_at") is None]
        rows.sort(key=lambda x: x["_id"], reverse=True)
        total = len(rows)
        page_rows = rows[page * page_size: page * page_size + page_size]
        items = [out for r in page_rows if (out := self._build_post_out(r)) is not None]
        return BatchPostsOut(total=total, count=len(items), items=items)

    def get_all(self, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        rows = [p for p in self.posts.values() if p.get("deleted_at") is None]
        rows.sort(key=lambda x: x["_id"], reverse=True)
        total = len(rows)
        page_rows = rows[page * page_size: page * page_size + page_size]
        items = [out for r in page_rows if (out := self._build_post_out(r)) is not None]
        return BatchPostsOut(total=total, count=len(items), items=items)

    # ========== 改 ==========

    def update(self, pid: str, data: PostDto) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted_at") is not None:
            return False

        # PATCH 语义：只更新显式传入字段
        if data.visibility is not None:
            post["post_status"].visibility = data.visibility
        if data.publish_status is not None:
            post["post_status"].publish_status = data.publish_status
        return True

    def update_content(self, pid: str, data: PostContentUpdate) -> bool:
        content = self.contents.get(pid)
        if not content:
            return False

        # PATCH 语义：只更新显式传入字段
        if data.title is not None:
            content.title = data.title
        if data.content is not None:
            content.content = data.content
        return True

    # ========== 删 ==========

    def soft_delete(self, pid: str) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted_at") is not None:
            return False
        post["deleted_at"] = self._now()
        return True

    def hard_delete(self, pid: str) -> bool:
        if pid not in self.posts:
            return False

        # 这里模拟 ORM 的 cascade：硬删 post 时连同 content/stats 一并清理。
        del self.posts[pid]
        self.contents.pop(pid, None)
        self.stats.pop(pid, None)
        return True

    # ========== 查（热榜） ==========

    def _get_author_out(self, uid: str) -> TopPostAuthorOut:
        username = "unknown"
        avatar_url = None
        if self._user_repo is not None:
            user = self._user_repo.find_user(uid=uid)
            if user is not None:
                username = user.user_info.username
                avatar_url = getattr(user.user_info, "avatar_url", None)
        return TopPostAuthorOut(uid=uid, username=username, avatar_url=avatar_url)

    def get_top_liked_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        cutoff = self._now() - timedelta(days=7)
        matched = []
        for pid, stats_dto in self.stats.items():
            post = self.posts.get(pid)
            if not post or post.get("deleted_at") is not None:
                continue
            content = self.contents.get(pid)
            if not content or content.created_at < cutoff:
                continue
            like_count = stats_dto.like_count or 0
            matched.append((like_count, post["_id"], pid, content.title, post["author_id"], stats_dto))

        # 对齐 SQLAlchemy repo 的排序策略：主键按计数倒序，次键用“更靠后写入”作为稳定排序。
        matched.sort(key=lambda x: (x[0], x[1]), reverse=True)

        items: List[TopPostOut] = []
        for _, _, pid, title, author_id, stats_dto in matched[:limit]:
            items.append(
                TopPostOut(
                    pid=pid,
                    title=title,
                    author=self._get_author_out(author_id),
                    post_stats=stats_dto,
                )
            )
        return items

    def get_top_commented_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        cutoff = self._now() - timedelta(days=7)
        matched = []
        for pid, stats_dto in self.stats.items():
            post = self.posts.get(pid)
            if not post or post.get("deleted_at") is not None:
                continue
            content = self.contents.get(pid)
            if not content or content.created_at < cutoff:
                continue
            comment_count = stats_dto.comment_count or 0
            matched.append((comment_count, post["_id"], pid, content.title, post["author_id"], stats_dto))

        matched.sort(key=lambda x: (x[0], x[1]), reverse=True)

        items: List[TopPostOut] = []
        for _, _, pid, title, author_id, stats_dto in matched[:limit]:
            items.append(
                TopPostOut(
                    pid=pid,
                    title=title,
                    author=self._get_author_out(author_id),
                    post_stats=stats_dto,
                )
            )
        return items
