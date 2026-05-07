import pytest

from tests.mock.mock_comment import MockCommentRepository
from app.schemas.v2.comment import (
    CommentCreate,
    CommentOnlyCreate,
    CommentQuery,
    StatusUpdate,
    CommentUpdate,
)


class TestMockCommentRepository:
    """测试 MockCommentRepository（聚合仓储）是否符合 ICommentRepository 协议约定。"""

    def test_create_and_get_by_cid(self):
        """意图：create_comment 创建评论聚合，get_by_cid 返回完整 CommentOut。"""
        repo = MockCommentRepository.empty()
        created = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="hello"))
        assert created.cid is not None
        assert created.comment_content.content == "hello"
        found = repo.get_by_cid(created.cid)
        assert found is not None
        assert found.cid == created.cid
        assert found.comment_content.content == "hello"
        assert found.like_count == 0
        assert found.comment_count == 0

    def test_soft_delete_hides_comment(self):
        """意图：soft_delete 后 get_by_cid 应返回 None。"""
        repo = MockCommentRepository.empty()
        c = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c"))
        assert repo.get_by_cid(c.cid) is not None
        assert repo.soft_delete(c.cid) is True
        assert repo.get_by_cid(c.cid) is None

    def test_soft_delete_twice_returns_false(self):
        """意图：重复 soft_delete 返回 False。"""
        repo = MockCommentRepository.empty()
        c = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c"))
        assert repo.soft_delete(c.cid) is True
        assert repo.soft_delete(c.cid) is False

    def test_hard_delete_removes_comment(self):
        """意图：hard_delete 后评论从存储中完全移除。"""
        repo = MockCommentRepository.empty()
        c = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c"))
        assert c.cid in repo.comments
        assert c.cid in repo.contents
        assert repo.hard_delete(c.cid) is True
        assert c.cid not in repo.comments
        assert c.cid not in repo.contents

    def test_hard_delete_nonexistent_returns_false(self):
        """意图：hard_delete 不存在的评论返回 False。"""
        repo = MockCommentRepository.empty()
        assert repo.hard_delete("nonexistent") is False

    def test_update_changes_status_and_review_status(self):
        """意图：update 可修改 status/review_status 字段。"""
        repo = MockCommentRepository.empty()
        c = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c"))
        assert repo.update(c.cid, StatusUpdate(status=1)) is True
        found = repo.get_by_cid(c.cid)
        assert found.status == 1
        assert repo.update(c.cid, StatusUpdate(review_status=1)) is True
        found2 = repo.get_by_cid(c.cid)
        assert found2.review_status == 1

    def test_update_nonexistent_returns_false(self):
        """意图：update 不存在的评论返回 False。"""
        repo = MockCommentRepository.empty()
        assert repo.update("nonexistent", StatusUpdate(status=1)) is False

    def test_update_counters(self):
        """意图：update_counters 增量更新点赞数和评论数。"""
        repo = MockCommentRepository.empty()
        c = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c"))
        assert repo.update_counters(c.cid, CommentUpdate(like_count_delta=5, comment_count_delta=3)) is True
        found = repo.get_by_cid(c.cid)
        assert found.like_count == 5
        assert found.comment_count == 3

    def test_update_counters_clamps_below_zero(self):
        """意图：update_counters 计数不应被更新到负数。"""
        repo = MockCommentRepository.empty()
        c = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c"))
        repo.update_counters(c.cid, CommentUpdate(like_count_delta=-10, comment_count_delta=-5))
        found = repo.get_by_cid(c.cid)
        assert found.like_count == 0
        assert found.comment_count == 0

    def test_get_comments_filters_by_post_id(self):
        """意图：get_comments 按 post_id 过滤。"""
        repo = MockCommentRepository.empty()
        repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c1"))
        repo.create_comment(CommentCreate(post_id="p1", author_id="a2", content="c2"))
        repo.create_comment(CommentCreate(post_id="p2", author_id="a1", content="c3"))
        result = repo.get_comments(CommentQuery(post_id="p1"), page=0, page_size=10)
        assert result.total == 2

    def test_get_comments_filters_by_author_id(self):
        """意图：get_comments 按 author_id 过滤。"""
        repo = MockCommentRepository.empty()
        repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="c1"))
        repo.create_comment(CommentCreate(post_id="p2", author_id="a1", content="c2"))
        repo.create_comment(CommentCreate(post_id="p2", author_id="a2", content="c3"))
        result = repo.get_comments(CommentQuery(author_id="a1"), page=0, page_size=10)
        assert result.total == 2

    def test_get_comments_pagination(self):
        """意图：get_comments 分页参数正确。"""
        repo = MockCommentRepository.empty()
        for i in range(5):
            repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content=f"c{i}"))
        result = repo.get_comments(CommentQuery(post_id="p1"), page=0, page_size=2)
        assert result.total == 5
        assert result.count == 2

    def test_get_by_cid_not_found_returns_none(self):
        """意图：不存在的 cid 返回 None。"""
        repo = MockCommentRepository.empty()
        assert repo.get_by_cid("nonexistent") is None

    def test_create_comment_sets_root_id_for_top_level(self):
        """意图：首层评论的 root_id 应设为自身 cid。"""
        repo = MockCommentRepository.empty()
        c = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="top-level"))
        assert c.root_id == c.cid

    def test_create_reply_preserves_root_id(self):
        """意图：回复评论保留 root_id。"""
        repo = MockCommentRepository.empty()
        parent = repo.create_comment(CommentCreate(post_id="p1", author_id="a1", content="parent"))
        reply = repo.create_comment(CommentCreate(post_id="p1", author_id="a2", content="reply", parent_id=parent.cid, root_id=parent.cid))
        assert reply.root_id == parent.cid
        assert reply.parent_id == parent.cid
