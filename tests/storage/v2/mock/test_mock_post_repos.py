import pytest

from tests.mock.mock_post import MockPostRepository
from tests.mock.mock_user import MockUserRepository
from app.schemas.v2.post import PostCreate, PostDto
from app.schemas.v2.post_content import PostContentUpdate
from app.schemas.v2.user import UserCreate


class TestMockPostRepository:
    """测试 MockPostRepository（聚合仓储）是否符合 IPostRepository 协议约定。"""

    def test_create_and_get_by_pid_should_include_content_and_stats(self):
        """意图：create_post 一次生成帖子聚合（基础信息 + content + stats），
        get_by_pid 应返回完整 PostOut。"""
        user_repo = MockUserRepository.empty()
        post_repo = MockPostRepository.empty(user_repo=user_repo)
        user_data = UserCreate(username="author", phone="111", password="pw")
        author = user_repo.create_user(user_data)
        created = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        out = post_repo.get_by_pid(created.pid)
        assert out is not None
        assert out.pid == created.pid
        assert out.post_content is not None
        assert out.post_content.title == "t"
        assert out.post_stats.like_count == 0
        assert out.post_stats.comment_count == 0

    def test_soft_delete_should_hide_post_from_queries(self):
        """意图：soft_delete 后，get_by_pid / get_by_author 都不应再返回该帖子。"""
        post_repo = MockPostRepository.empty()
        created = post_repo.create_post(
            PostCreate(author_id="a", title="t", content="c", post_status=PostDto())
        )
        assert post_repo.get_by_pid(created.pid) is not None
        assert post_repo.soft_delete(created.pid) is True
        assert post_repo.get_by_pid(created.pid) is None
        batch = post_repo.get_by_author("a", page=0, page_size=10)
        assert batch.total == 0
        assert batch.count == 0

    def test_hard_delete_should_remove_post_aggregate(self):
        """意图：hard_delete 后，帖子聚合应从存储中完全移除（含 content/stats）。"""
        post_repo = MockPostRepository.empty()
        created = post_repo.create_post(
            PostCreate(author_id="a", title="t", content="c", post_status=PostDto())
        )
        assert created.pid in post_repo.posts
        assert created.pid in post_repo.contents
        assert created.pid in post_repo.stats
        assert post_repo.hard_delete(created.pid) is True
        assert created.pid not in post_repo.posts
        assert created.pid not in post_repo.contents
        assert created.pid not in post_repo.stats

    def test_update_content_should_patch_only_provided_fields(self):
        """意图：update_content 遵循 PATCH 语义，仅更新显式传入的字段。"""
        post_repo = MockPostRepository.empty()
        created = post_repo.create_post(
            PostCreate(author_id="a", title="t", content="c", post_status=PostDto())
        )
        ok = post_repo.update_content(created.pid, PostContentUpdate(title="t2"))
        assert ok is True
        out = post_repo.get_by_pid(created.pid)
        assert out.post_content.title == "t2"
        assert out.post_content.content == "c"

    def test_get_top_liked_with_posts_should_sort_by_like_count_desc(self):
        """意图：get_top_liked_with_posts 按 like_count 倒序返回。"""
        post_repo = MockPostRepository.empty()
        p1 = post_repo.create_post(
            PostCreate(author_id="a", title="t1", content="c1", post_status=PostDto())
        )
        p2 = post_repo.create_post(
            PostCreate(author_id="a", title="t2", content="c2", post_status=PostDto())
        )
        post_repo.stats[p1.pid].like_count = 1
        post_repo.stats[p2.pid].like_count = 10
        out = post_repo.get_top_liked_with_posts(limit=10)
        assert len(out) == 2
        assert out[0].pid == p2.pid

    def test_get_top_commented_with_posts_should_return_ordered(self):
        """意图：get_top_commented_with_posts 按 comment_count 倒序返回。"""
        post_repo = MockPostRepository.empty()
        p1 = post_repo.create_post(
            PostCreate(author_id="a", title="t1", content="c1", post_status=PostDto())
        )
        p2 = post_repo.create_post(
            PostCreate(author_id="a", title="t2", content="c2", post_status=PostDto())
        )
        post_repo.stats[p1.pid].comment_count = 5
        post_repo.stats[p2.pid].comment_count = 15
        out = post_repo.get_top_commented_with_posts(limit=10)
        assert len(out) == 2
        assert out[0].pid == p2.pid

    def test_get_by_author_pagination(self):
        """意图：get_by_author 分页参数正确。"""
        post_repo = MockPostRepository.empty()
        for i in range(5):
            post_repo.create_post(
                PostCreate(author_id="a", title=f"p{i}", content="c", post_status=PostDto())
            )
        batch = post_repo.get_by_author("a", page=0, page_size=2)
        assert batch.total == 5
        assert batch.count == 2
        assert len(batch.items) == 2

    def test_get_all_filters_deleted(self):
        """意图：get_all 应过滤已软删除的帖子。"""
        post_repo = MockPostRepository.empty()
        p1 = post_repo.create_post(
            PostCreate(author_id="a", title="t1", content="c", post_status=PostDto())
        )
        p2 = post_repo.create_post(
            PostCreate(author_id="b", title="t2", content="c", post_status=PostDto())
        )
        post_repo.soft_delete(p1.pid)
        batch = post_repo.get_all(page=0, page_size=10)
        assert batch.total == 1
        assert batch.items[0].pid == p2.pid

    def test_hard_delete_nonexistent_returns_false(self):
        """意图：hard_delete 不存在的帖子返回 False。"""
        post_repo = MockPostRepository.empty()
        assert post_repo.hard_delete("nonexistent") is False

    def test_update_nonexistent_returns_false(self):
        """意图：update 不存在的帖子返回 False。"""
        post_repo = MockPostRepository.empty()
        assert post_repo.update("nonexistent", PostDto(visibility=1)) is False

    def test_soft_delete_nonexistent_returns_false(self):
        """意图：soft_delete 不存在的帖子返回 False。"""
        post_repo = MockPostRepository.empty()
        assert post_repo.soft_delete("nonexistent") is False

    def test_update_content_nonexistent_returns_false(self):
        """意图：update_content 不存在的帖子返回 False。"""
        post_repo = MockPostRepository.empty()
        assert post_repo.update_content("nonexistent", PostContentUpdate(title="x")) is False

    def test_soft_delete_twice_returns_false(self):
        """意图：重复 soft_delete 返回 False。"""
        post_repo = MockPostRepository.empty()
        c = post_repo.create_post(PostCreate(author_id="a", title="t", content="c", post_status=PostDto()))
        assert post_repo.soft_delete(c.pid) is True
        assert post_repo.soft_delete(c.pid) is False
