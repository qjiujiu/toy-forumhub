import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from app.schemas.v2.post import (
    BatchPostsOut,
    PostCreate,
    PostDto,
    PostOnlyCreate,
    PostOut,
    TopPostAuthorOut,
    TopPostOut,
)
from app.schemas.v2.post_content import PostContentCreate, PostContentOut, PostContentUpdate
from app.schemas.v2.post_stats import BatchPostStatsOut, PostStatsCreate, PostStatsOut, PostStatsDto


class MockPostRepository:
    def __init__(self, content_repo=None, stats_repo=None):
        # posts[pid] = {"pid": str, "author_id": str, "post_status": PostDto, "deleted": bool}
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

    def create_post(self, data: PostCreate) -> PostOut:
        """创建帖子聚合（mock 版）。

        说明：
        - 真实 SQLAlchemy repo 会在一个事务里写入三表。
        - mock 版没有数据库，所以用三个内存仓库来模拟三张表。
        - 关键在于“对外只暴露一个仓储入口”：上层只关心 create_post，而不关心三表细节。
        """
        pid = self.create(PostOnlyCreate(author_id=data.author_id, post_status=data.post_status))

        if self._content_repo:
            self._content_repo.create(PostContentCreate(post_id=pid, title=data.title, content=data.content))
        if self._stats_repo:
            self._stats_repo.create(PostStatsCreate(post_id=pid, post_stats=PostStatsDto()))

        out = self.get_by_pid(pid)
        if not out:
            raise RuntimeError(f"post {pid} not found after creation")
        return out

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

    def update_content(self, pid: str, data: PostContentUpdate) -> bool:
        # 这里直接委托给内容仓库；如果你未来希望“真正合并对象”，也可以把内容字典直接放进 MockPostRepository。
        if not self._content_repo:
            return False
        return self._content_repo.update(pid, data)

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

        # 下面这个参数其实是没有什么作用的,
        # 放在这个地方仅仅是为了格式能跟真实的 repo 对象保持一致
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

    def update(self, post_id: str, data: PostContentUpdate) -> bool:
        content = self.contents.get(post_id)
        if not content:
            return False
        if data.title is not None:
            content.title = data.title
        if data.content is not None:
            content.content = data.content
        return True


class MockPostStatsRepository:
    def __init__(self, post_repo, user_repo=None):
        self.stats: Dict[str, PostStatsDto] = {}
        self.post_repo = post_repo
        self.user_repo = user_repo

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
            stats_dto.like_count = max(0, (stats_dto.like_count or 0) + delta)
        if data.comment_count is not None:
            stats_dto.comment_count = max(0, (stats_dto.comment_count or 0) + delta)
        return True

    def get_top_liked(self, limit: int = 10) -> BatchPostStatsOut:
        """返回按 like_count 排序的 PostStatsOut 列表（只含 stats，不含 post 信息）。"""
        items: List[PostStatsOut] = []
        for post_id, stats_dto in self.stats.items():
            if self.post_repo.posts.get(post_id, {}).get("deleted"):
                continue
            items.append(PostStatsOut(psid=str(uuid.uuid4()), post_id=post_id, post_stats=stats_dto))
        items.sort(key=lambda x: x.post_stats.like_count or 0, reverse=True)
        top = items[:limit]
        return BatchPostStatsOut(total=len(items), count=len(top), items=top)

    def get_top_commented(self, limit: int = 10) -> BatchPostStatsOut:
        """返回按 comment_count 排序的 PostStatsOut 列表（只含 stats，不含 post 信息）。"""
        items: List[PostStatsOut] = []
        for post_id, stats_dto in self.stats.items():
            if self.post_repo.posts.get(post_id, {}).get("deleted"):
                continue
            items.append(PostStatsOut(psid=str(uuid.uuid4()), post_id=post_id, post_stats=stats_dto))
        items.sort(key=lambda x: x.post_stats.comment_count or 0, reverse=True)
        top = items[:limit]
        return BatchPostStatsOut(total=len(items), count=len(top), items=top)

    def get_top_liked_with_posts(self, limit: int = 10) -> list:
        cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=7)
        matched = []
        for post_id, stats_dto in self.stats.items():
            post = self.post_repo.posts.get(post_id)
            if not post or post.get("deleted"):
                continue
            content = self.post_repo._content_repo.get_by_post_id(post_id) if self.post_repo._content_repo else None
            if not content or content.created_at < cutoff:
                continue

            author_id = post["author_id"]
            username = "unknown"
            if self.user_repo is not None:
                user = self.user_repo.find_user(uid=author_id)
                if user:
                    username = user.user_info.username
            matched.append((post_id, stats_dto.like_count or 0, content.title, author_id, username, stats_dto))

        matched.sort(key=lambda x: x[1], reverse=True)
        items: List[TopPostOut] = []
        for post_id, _, title, author_id, username, stats_dto in matched[:limit]:
            items.append(
                TopPostOut(
                    pid=post_id,
                    title=title,
                    author=TopPostAuthorOut(uid=author_id, username=username),
                    post_stats=stats_dto,
                )
            )
        return items

    def get_top_commented_with_posts(self, limit: int = 10) -> list:
        cutoff = datetime.now(timezone(timedelta(hours=8))) - timedelta(days=7)
        matched = []
        for post_id, stats_dto in self.stats.items():
            post = self.post_repo.posts.get(post_id)
            if not post or post.get("deleted"):
                continue
            content = self.post_repo._content_repo.get_by_post_id(post_id) if self.post_repo._content_repo else None
            if not content or content.created_at < cutoff:
                continue

            author_id = post["author_id"]
            username = "unknown"
            if self.user_repo is not None:
                user = self.user_repo.find_user(uid=author_id)
                if user:
                    username = user.user_info.username
            matched.append((post_id, stats_dto.comment_count or 0, content.title, author_id, username, stats_dto))

        matched.sort(key=lambda x: x[1], reverse=True)
        items: List[TopPostOut] = []
        for post_id, _, title, author_id, username, stats_dto in matched[:limit]:
            items.append(
                TopPostOut(
                    pid=post_id,
                    title=title,
                    author=TopPostAuthorOut(uid=author_id, username=username),
                    post_stats=stats_dto,
                )
            )
        return items


# 为了让“聚合仓储”对外只暴露一个对象，我们把热榜方法也挂到 MockPostRepository 上。
# 这和真实 SQLAlchemyPostRepository 的升级方向一致。
def _mock_repo_get_top_liked_with_posts(self: MockPostRepository, limit: int = 10) -> list:
    if not self._stats_repo:
        return []
    return self._stats_repo.get_top_liked_with_posts(limit)


def _mock_repo_get_top_commented_with_posts(self: MockPostRepository, limit: int = 10) -> list:
    if not self._stats_repo:
        return []
    return self._stats_repo.get_top_commented_with_posts(limit)


# 动态挂载方法（Python 的函数是一等公民，这是一个教学点）：
# - 这里用“函数赋值”的方式给类补方法，避免大段复制粘贴。
# - 真实项目里一般不建议这么做（可读性差），但作为教学示例可以帮助理解“对象本质上是可变的”。
MockPostRepository.get_top_liked_with_posts = _mock_repo_get_top_liked_with_posts
MockPostRepository.get_top_commented_with_posts = _mock_repo_get_top_commented_with_posts
