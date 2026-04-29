import pytest

from app.schemas.v2.post import PostCreate, PostDto, PostOnlyCreate
from app.schemas.v2.post_content import PostContentCreate, PostContentUpdate
from app.schemas.v2.post_stats import PostStatsCreate, PostStatsDto

from app.storage.v2.mock.mock_post import (
    MockPostRepository,
    MockPostContentRepository,
    MockPostStatsRepository,
)
from app.storage.v2.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate


class TestMockPostRepository:
    def test_create_and_get_by_pid_should_include_content_and_stats(self):
        """
        测试意图：创建 post/content/stats 之后, 通过 get_by_pid 应返回聚合的 PostOut。
        """
        post_repo = MockPostRepository()
        content_repo = MockPostContentRepository(post_repo)
        user_repo = MockUserRepository()
        stats_repo = MockPostStatsRepository(post_repo, user_repo=user_repo)
        post_repo.set_related_repos(content_repo, stats_repo)

        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        pid = post_repo.create(PostOnlyCreate(author_id=author.uid, post_status=PostDto(publish_status=0)))
        content_repo.create(PostContentCreate(post_id=pid, title="t", content="c"))
        stats_repo.create(PostStatsCreate(post_id=pid, post_stats=PostStatsDto(like_count=0, comment_count=0)))

        out = post_repo.get_by_pid(pid)
        assert out is not None
        assert out.pid == pid
        assert out.post_content is not None
        assert out.post_content.title == "t"
        assert out.post_stats.like_count == 0
        assert out.post_stats.comment_count == 0

    def test_soft_delete_should_hide_post_from_queries(self):
        """意图：soft_delete 后，get_by_pid/get_by_author 都不应再返回该帖子。"""
        post_repo = MockPostRepository()
        content_repo = MockPostContentRepository(post_repo)
        stats_repo = MockPostStatsRepository(post_repo)
        post_repo.set_related_repos(content_repo, stats_repo)

        pid = post_repo.create(PostOnlyCreate(author_id="a", post_status=PostDto(publish_status=0)))
        content_repo.create(PostContentCreate(post_id=pid, title="t", content="c"))
        stats_repo.create(PostStatsCreate(post_id=pid, post_stats=PostStatsDto(like_count=0, comment_count=0)))

        assert post_repo.get_by_pid(pid) is not None
        assert post_repo.soft_delete(pid) is True
        assert post_repo.get_by_pid(pid) is None

        batch = post_repo.get_by_author("a", page=0, page_size=10)
        assert batch.total == 0
        assert batch.count == 0

    def test_hard_delete_should_remove_post(self):
        """意图：hard_delete 后，帖子应从存储中移除。"""
        post_repo = MockPostRepository()
        pid = post_repo.create(PostOnlyCreate(author_id="a", post_status=PostDto(publish_status=0)))
        assert pid in post_repo.posts

        assert post_repo.hard_delete(pid) is True
        assert pid not in post_repo.posts


class TestMockPostContentRepository:
    def test_update_should_patch_only_provided_fields(self):
        """意图：update 仅更新显式传入字段，未传字段保持不变。"""
        post_repo = MockPostRepository()
        repo = MockPostContentRepository(post_repo)

        pid = "p"
        repo.create(PostContentCreate(post_id=pid, title="t", content="c"))

        ok = repo.update(pid, PostContentUpdate(title="t2"))
        assert ok is True
        out = repo.get_by_post_id(pid)
        assert out is not None
        assert out.title == "t2"
        assert out.content == "c"


class TestMockPostStatsRepository:
    def test_update_should_not_make_counts_negative(self):
        """意图：update 的增量更新不应把计数更新为负数。"""
        post_repo = MockPostRepository()
        repo = MockPostStatsRepository(post_repo)

        pid = "p"
        repo.create(PostStatsCreate(post_id=pid, post_stats=PostStatsDto(like_count=0, comment_count=0)))

        assert repo.update(pid, PostStatsDto(like_count=1), delta=1) is True
        assert repo.update(pid, PostStatsDto(like_count=1), delta=-100) is True
        out = repo.get_by_post_id(pid)
        assert out is not None
        assert out.post_stats.like_count == 0

    def test_get_top_liked_should_sort_by_like_count_desc(self):
        """意图：get_top_liked 按点赞数倒序返回。"""
        post_repo = MockPostRepository()
        repo = MockPostStatsRepository(post_repo)

        # 需要给 post_repo 塞入未删除的帖子，否则 top_* 会过滤 deleted
        p1 = post_repo.create(PostOnlyCreate(author_id="a", post_status=PostDto()))
        p2 = post_repo.create(PostOnlyCreate(author_id="a", post_status=PostDto()))
        repo.create(PostStatsCreate(post_id=p1, post_stats=PostStatsDto(like_count=1, comment_count=0)))
        repo.create(PostStatsCreate(post_id=p2, post_stats=PostStatsDto(like_count=10, comment_count=0)))

        out = repo.get_top_liked(limit=10)
        assert out.count == 2
        assert out.items[0].post_id == p2
