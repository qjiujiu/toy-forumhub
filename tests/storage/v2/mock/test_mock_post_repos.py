
from app.schemas.v2.post import PostCreate, PostDto
from app.schemas.v2.post_content import PostContentUpdate
from app.storage.v2.mock.mock_post import MockPostRepository
from app.storage.v2.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate
import pytest


class TestMockPostRepository:
    def test_create_and_get_by_pid_should_include_content_and_stats(self):
        """
        测试意图：通过聚合仓储 create_post 创建帖子后，get_by_pid 应返回完整的 PostOut。

        知识点：
        - mock repo 也应对齐“聚合仓储”的抽象：上层不应该再组装 content_repo/stats_repo。
        - 物理三表的细节，被 mock repo 内部的 3 份内存字典隐藏起来。
        """
        user_repo = MockUserRepository()
        post_repo = MockPostRepository(user_repo=user_repo)

        user_data = UserCreate(username="author", phone="111", password="pw")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)
        created = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto(publish_status=0))
        )

        out = post_repo.get_by_pid(created.pid)
        assert out is not None
        assert out.pid == created.pid
        assert out.post_content is not None
        assert out.post_content.title == "t"
        assert out.post_stats.like_count == 0
        assert out.post_stats.comment_count == 0

    def test_soft_delete_should_hide_post_from_queries(self):
        """意图：soft_delete 后，get_by_pid/get_by_author 都不应再返回该帖子。"""
        post_repo = MockPostRepository()
        created = post_repo.create_post(PostCreate(author_id="a", title="t", content="c", post_status=PostDto(publish_status=0)))

        assert post_repo.get_by_pid(created.pid) is not None
        assert post_repo.soft_delete(created.pid) is True
        assert post_repo.get_by_pid(created.pid) is None

        batch = post_repo.get_by_author("a", page=0, page_size=10)
        assert batch.total == 0
        assert batch.count == 0

    def test_hard_delete_should_remove_post(self):
        """意图：hard_delete 后，帖子聚合应从存储中移除（含 content/stats）。"""
        post_repo = MockPostRepository()
        created = post_repo.create_post(PostCreate(author_id="a", title="t", content="c", post_status=PostDto(publish_status=0)))
        assert created.pid in post_repo.posts
        assert created.pid in post_repo.contents
        assert created.pid in post_repo.stats

        assert post_repo.hard_delete(created.pid) is True
        assert created.pid not in post_repo.posts
        assert created.pid not in post_repo.contents
        assert created.pid not in post_repo.stats

    def test_update_content_should_patch_only_provided_fields(self):
        """意图：update_content 遵循 PATCH 语义，仅更新显式字段。"""
        post_repo = MockPostRepository()
        created = post_repo.create_post(PostCreate(author_id="a", title="t", content="c", post_status=PostDto(publish_status=0)))

        ok = post_repo.update_content(created.pid, PostContentUpdate(title="t2"))
        assert ok is True

        out = post_repo.get_by_pid(created.pid)
        assert out is not None
        assert out.post_content.title == "t2"
        assert out.post_content.content == "c"

    def test_get_top_liked_with_posts_should_sort_by_like_count_desc(self):
        """意图：get_top_liked_with_posts 按 like_count 倒序返回。"""
        post_repo = MockPostRepository()
        p1 = post_repo.create_post(PostCreate(author_id="a", title="t1", content="c1", post_status=PostDto()))
        p2 = post_repo.create_post(PostCreate(author_id="a", title="t2", content="c2", post_status=PostDto()))

        # 说明：PostStatsDto 不在 IPostRepository 里提供更新接口，这里直接改 mock 的内部状态用于测试排序。
        post_repo.stats[p1.pid].like_count = 1
        post_repo.stats[p2.pid].like_count = 10

        out = post_repo.get_top_liked_with_posts(limit=10)
        assert len(out) == 2
        assert out[0].pid == p2.pid
