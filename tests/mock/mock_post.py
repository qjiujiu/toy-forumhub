import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from app.schemas.v2.post import PostOnlyCreate, PostOut, BatchPostsOut, PostDto
from app.schemas.v2.post_content import PostContentCreate, PostContentOut
from app.schemas.v2.post_stats import PostStatsCreate, PostStatsOut, PostStatsDto
from app.models.v2.post import PostVisibility, PostPublishStatus


class MockPostRepository:
    def __init__(self, content_repo=None, stats_repo=None):
        self.posts: Dict[str, dict] = {}
        self._content_repo = content_repo
        self._stats_repo = stats_repo

    def set_related_repos(self, content_repo, stats_repo):
        self._content_repo = content_repo
        self._stats_repo = stats_repo

    def create(self, data: PostOnlyCreate) -> str:
        pid = str(uuid.uuid4())
        status = data.post_status
        if status is None or status.publish_status is None:
            status = PostDto(publish_status=0)
        self.posts[pid] = {
            "pid": pid,
            "author_id": data.author_id,
            "post_status": status,
        }
        return pid

    def get_by_pid(self, pid: str) -> Optional[PostOut]:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return None

        content = None
        stats = None
        if self._content_repo:
            content = self._content_repo.get_by_post_id(pid)
        if self._stats_repo:
            stats_out = self._stats_repo.get_by_post_id(pid)
            if stats_out:
                stats = stats_out.post_stats

        return PostOut(
            pid=post["pid"],
            author_id=post["author_id"],
            post_status=post["post_status"],
            post_content=content,
            post_stats=stats or PostStatsDto(),
        )

    def get_by_author(self, author_id: str, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        matched = []
        for p in self.posts.values():
            if p["author_id"] == author_id and not p.get("deleted"):
                post_out = self.get_by_pid(p["pid"])
                if post_out:
                    matched.append(post_out)
        matched.sort(key=lambda x: x.post_content.created_at if x.post_content else datetime.min, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchPostsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    def get_all(self, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        matched = []
        for p in self.posts.values():
            if not p.get("deleted"):
                post_out = self.get_by_pid(p["pid"])
                if post_out:
                    matched.append(post_out)
        matched.sort(key=lambda x: x.post_content.created_at if x.post_content else datetime.min, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchPostsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    def update(self, pid: str, data: PostDto) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return False
        if data.visibility is not None:
            post["post_status"].visibility = data.visibility
        if data.publish_status is not None:
            post["post_status"].publish_status = data.publish_status
        return True

    def soft_delete(self, pid: str) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return False
        post["deleted"] = True
        return True

    def hard_delete(self, pid: str) -> bool:
        if pid in self.posts:
            del self.posts[pid]
            return True
        return False
        matched = [p for p in self.posts.values() if p.author_id == author_id and not self._is_soft_deleted(p)]
        matched.sort(key=lambda x: x.post_content.created_at if x.post_content else datetime.min, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchPostsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    def get_all(self, page: int = 0, page_size: int = 20) -> BatchPostsOut:
        matched = []
        for p in self.posts.values():
            if not p.get("deleted"):
                post_out = self.get_by_pid(p["pid"])
                if post_out:
                    matched.append(post_out)
        matched.sort(key=lambda x: x.post_content.created_at if x.post_content else datetime.min, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchPostsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    def update(self, pid: str, data: PostDto) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return False
        if data.visibility is not None:
            post["post_status"].visibility = data.visibility
        if data.publish_status is not None:
            post["post_status"].publish_status = data.publish_status
        return True

    def soft_delete(self, pid: str) -> bool:
        post = self.posts.get(pid)
        if not post or post.get("deleted"):
            return False
        post["deleted"] = True
        return True

    def hard_delete(self, pid: str) -> bool:
        if pid in self.posts:
            del self.posts[pid]
            return True
        return False


class MockPostContentRepository:
    def __init__(self, post_repo):
        self.contents: Dict[str, PostContentOut] = {}
        self.post_repo = post_repo

    def create(self, data: PostContentCreate) -> str:
        pcid = str(uuid.uuid4())
        now = datetime.now(timezone(timedelta(hours=8)))
        content = PostContentOut(
            pcid=pcid,
            post_id=data.post_id,
            title=data.title,
            content=data.content,
            created_at=now,
        )
        self.contents[data.post_id] = content
        return pcid

    def get_by_post_id(self, post_id: str) -> Optional[PostContentOut]:
        return self.contents.get(post_id)

    def update(self, post_id: str, data) -> bool:
        content = self.contents.get(post_id)
        if not content:
            return False
        if data.title is not None:
            content.title = data.title
        if data.content is not None:
            content.content = data.content
        return True


class MockPostStatsRepository:
    def __init__(self, post_repo):
        self.stats: Dict[str, PostStatsDto] = {}
        self.post_repo = post_repo

    def create(self, data: PostStatsCreate) -> str:
        psid = str(uuid.uuid4())
        stats_dto = PostStatsDto(
            like_count=data.post_stats.like_count or 0,
            comment_count=data.post_stats.comment_count or 0,
        )
        self.stats[data.post_id] = stats_dto
        return psid

    def get_by_post_id(self, post_id: str) -> Optional[PostStatsOut]:
        stats_dto = self.stats.get(post_id)
        if not stats_dto:
            return None
        return PostStatsOut(
            psid=str(uuid.uuid4()),
            post_id=post_id,
            post_stats=stats_dto,
        )

    def update(self, post_id: str, data: PostStatsDto, delta: int = 1) -> bool:
        stats_dto = self.stats.get(post_id)
        if not stats_dto:
            return False
        if data.like_count is not None:
            stats_dto.like_count = max(0, stats_dto.like_count + delta)
        if data.comment_count is not None:
            stats_dto.comment_count = max(0, stats_dto.comment_count + delta)
        return True

    def delete(self, post_id: str) -> bool:
        if post_id in self.stats:
            del self.stats[post_id]
            return True
        return False

    def get_top_liked_with_posts(self, limit: int = 10) -> list:
        from app.schemas.v2.post import TopPostOut, TopPostAuthorOut
        from app.schemas.v2.post_stats import PostStatsDto

        cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=7)
        matched = []
        for post_id, stats_dto in self.stats.items():
            post = self.post_repo.posts.get(post_id)
            if not post or post.get("deleted"):
                continue
            content = self.post_repo._content_repo.get_by_post_id(post_id) if self.post_repo._content_repo else None
            if content and content.created_at >= cutoff:
                author_id = post["author_id"]
                user = self.post_repo._stats_repo.user_repo.find_user(uid=author_id) if self.post_repo._stats_repo and hasattr(self.post_repo._stats_repo, 'user_repo') else None
                username = user.user_info.username if user else "unknown"
                matched.append((post_id, stats_dto.like_count, content.title, author_id, username))
        
        matched.sort(key=lambda x: x[1], reverse=True)
        items = []
        for post_id, like_count, title, author_id, username in matched[:limit]:
            stats_dto = self.stats.get(post_id, PostStatsDto())
            items.append(TopPostOut(
                pid=post_id,
                title=title,
                author=TopPostAuthorOut(uid=author_id, username=username),
                post_stats=stats_dto,
            ))
        return items

    def get_top_commented_with_posts(self, limit: int = 10) -> list:
        from app.schemas.v2.post import TopPostOut, TopPostAuthorOut
        from app.schemas.v2.post_stats import PostStatsDto

        cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=7)
        matched = []
        for post_id, stats_dto in self.stats.items():
            post = self.post_repo.posts.get(post_id)
            if not post or post.get("deleted"):
                continue
            content = self.post_repo._content_repo.get_by_post_id(post_id) if self.post_repo._content_repo else None
            if content and content.created_at >= cutoff:
                author_id = post["author_id"]
                user = self.post_repo._stats_repo.user_repo.find_user(uid=author_id) if self.post_repo._stats_repo and hasattr(self.post_repo._stats_repo, 'user_repo') else None
                username = user.user_info.username if user else "unknown"
                matched.append((post_id, stats_dto.comment_count, content.title, author_id, username))
        
        matched.sort(key=lambda x: x[1], reverse=True)
        items = []
        for post_id, comment_count, title, author_id, username in matched[:limit]:
            stats_dto = self.stats.get(post_id, PostStatsDto())
            items.append(TopPostOut(
                pid=post_id,
                title=title,
                author=TopPostAuthorOut(uid=author_id, username=username),
                post_stats=stats_dto,
            ))
        return items