"""
聚合仓储风格的 MockPostRepository。

物理上 posts / post_contents / post_stats 是三张独立表，
本 Mock 用一个对象内部维护三份字典，屏蔽多表细节，
对外以"一个帖子聚合"的形式提供读写能力，对齐 IPostRepository 协议。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from app.schemas.v2.post import (
    PostCreate,
    PostOnlyCreate,
    PostOut,
    BatchPostsOut,
    PostDto,
    TopPostOut,
    TopPostAuthorOut,
)
from app.schemas.v2.post_content import PostContentCreate, PostContentOut, PostContentUpdate
from app.schemas.v2.post_stats import PostStatsCreate, PostStatsDto, PostStatsOut


def _now():
    return datetime.now(timezone(timedelta(hours=8)))


class MockPostRepository:
    """Mock 聚合仓储：内部维护 posts/contents/stats 三份字典，对外以聚合方式操作。"""

    def __init__(self, user_repo=None):
        self.posts: Dict[str, dict] = {}
        self.contents: Dict[str, PostContentOut] = {}
        self.stats: Dict[str, PostStatsDto] = {}
        self._user_repo = user_repo

    @classmethod
    def empty(cls, user_repo=None):
        """返回一个空仓库（无预置数据），方便单测从零开始。"""
        return cls(user_repo=user_repo)

    # ========== 增 ==========

    def create(self, data: PostOnlyCreate) -> str:
        pid = str(uuid.uuid4())
        status = data.post_status or PostDto()
        self.posts[pid] = {
            "pid": pid,
            "author_id": data.author_id,
            "visibility": status.visibility.value if status.visibility is not None else 0,
            "publish_status": status.publish_status.value if status.publish_status is not None else 0,
            "deleted": False,
        }
        return pid

    def create_post(self, data: PostCreate) -> PostOut:
        pid = self.create(PostOnlyCreate(author_id=data.author_id, post_status=data.post_status))
        now = _now()

        content = PostContentOut(
            pcid=str(uuid.uuid4()),
            post_id=pid,
            title=data.title,
            content=data.content,
            created_at=now,
        )
        self.contents[pid] = content

        stats = PostStatsDto(like_count=0, comment_count=0)
        self.stats[pid] = stats

        return PostOut(
            pid=pid,
            author_id=data.author_id,
            post_status=PostDto.model_validate(self.posts[pid]),
            post_content=content,
            post_stats=stats,
        )

    # ========== 查 ==========

    def get_by_pid(self, pid: str) -> Optional[PostOut]:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return None

        content = self.contents.get(pid)
        if not content:
            return None

        stats = self.stats.get(pid, PostStatsDto(like_count=0, comment_count=0))
        return PostOut(
            pid=post["pid"],
            author_id=post["author_id"],
            post_status=PostDto(
                visibility=post["visibility"],
                publish_status=post["publish_status"],
            ),
            post_content=content,
            post_stats=stats,
        )

    def get_by_author(self, author_id: str, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        matched = []
        for p in self.posts.values():
            if p["author_id"] == author_id and not p.get("deleted"):
                out = self.get_by_pid(p["pid"])
                if out:
                    matched.append(out)
        matched.sort(key=lambda x: x.post_content.created_at, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchPostsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    def get_all(self, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        matched = []
        for p in self.posts.values():
            if not p.get("deleted"):
                out = self.get_by_pid(p["pid"])
                if out:
                    matched.append(out)
        matched.sort(key=lambda x: x.post_content.created_at, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchPostsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    # ========== 改 ==========

    def update(self, pid: str, data: PostDto) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return False
        if data.visibility is not None:
            post["visibility"] = data.visibility.value
        if data.publish_status is not None:
            post["publish_status"] = data.publish_status.value
        return True

    def update_content(self, pid: str, data: PostContentUpdate) -> bool:
        content = self.contents.get(pid)
        if not content:
            return False
        if data.title is not None:
            content.title = data.title
        if data.content is not None:
            content.content = data.content
        return True

    # ========== 删 ==========

    def soft_delete(self, pid: str) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return False
        post["deleted"] = True
        return True

    def hard_delete(self, pid: str) -> bool:
        if pid not in self.posts:
            return False
        del self.posts[pid]
        self.contents.pop(pid, None)
        self.stats.pop(pid, None)
        return True

    # ========== 热榜 ==========

    def get_top_liked_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        cutoff = _now() - timedelta(days=7)
        matched = []
        for pid, stats_dto in self.stats.items():
            post = self.posts.get(pid)
            if not post or post.get("deleted"):
                continue
            content = self.contents.get(pid)
            if not content or content.created_at < cutoff:
                continue
            author_id = post["author_id"]
            username = "unknown"
            if self._user_repo:
                user = self._user_repo.find_user(uid=author_id)
                if user:
                    username = user.user_info.username or "unknown"
            matched.append((pid, stats_dto.like_count or 0, content.title, author_id, username))
        matched.sort(key=lambda x: x[1], reverse=True)
        return [
            TopPostOut(
                pid=pid,
                title=title,
                author=TopPostAuthorOut(uid=author_id, username=username),
                post_stats=PostStatsDto(like_count=lc, comment_count=0),
            )
            for pid, lc, title, author_id, username in matched[:limit]
        ]

    def get_top_commented_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        cutoff = _now() - timedelta(days=7)
        matched = []
        for pid, stats_dto in self.stats.items():
            post = self.posts.get(pid)
            if not post or post.get("deleted"):
                continue
            content = self.contents.get(pid)
            if not content or content.created_at < cutoff:
                continue
            author_id = post["author_id"]
            username = "unknown"
            if self._user_repo:
                user = self._user_repo.find_user(uid=author_id)
                if user:
                    username = user.user_info.username or "unknown"
            matched.append((pid, stats_dto.comment_count or 0, content.title, author_id, username))
        matched.sort(key=lambda x: x[1], reverse=True)
        return [
            TopPostOut(
                pid=pid,
                title=title,
                author=TopPostAuthorOut(uid=author_id, username=username),
                post_stats=PostStatsDto(like_count=0, comment_count=cc),
            )
            for pid, cc, title, author_id, username in matched[:limit]
        ]
