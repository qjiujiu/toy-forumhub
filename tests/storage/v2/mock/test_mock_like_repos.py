import pytest

from tests.mock.mock_like import MockLikeRepository
from app.schemas.v2.like import LikeCreate, LikeCancel, LikeDto
from app.core.exceptions import AlreadyLikedError, NotLikedError


class TestMockLikeRepository:
    """测试 MockLikeRepository 是否符合 ILikeRepository 协议约定。"""

    # ==================== C ====================

    def test_create_new_like(self):
        """意图：create_or_restore 创建新点赞，返回完整 LikeOut。"""
        repo = MockLikeRepository.empty()
        result = repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        assert result.lid is not None
        assert result.user_id == "u1"
        assert result.target_type == 0
        assert result.target_id == "p1"

    def test_create_duplicate_raises(self):
        """意图：重复点赞且未取消 → 抛 AlreadyLikedError。"""
        repo = MockLikeRepository.empty()
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        with pytest.raises(AlreadyLikedError):
            repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))

    def test_restore_cancelled_like(self):
        """意图：先取消再点赞 → 恢复成功（不会创建新记录）。"""
        repo = MockLikeRepository.empty()
        created = repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        repo.cancel(LikeCancel(user_id="u1", target_type=0, target_id="p1"))
        restored = repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        assert restored.lid == created.lid
        assert restored.user_id == "u1"

    def test_create_like_target_type_comment(self):
        """意图：为评论点赞。"""
        repo = MockLikeRepository.empty()
        result = repo.create_or_restore(LikeCreate(user_id="u1", target_type=1, target_id="c1"))
        assert result.target_type == 1
        assert result.target_id == "c1"

    # ==================== D ====================

    def test_cancel_existing_like(self):
        """意图：取消存在的有效点赞 → 返回 True。"""
        repo = MockLikeRepository.empty()
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        assert repo.cancel(LikeCancel(user_id="u1", target_type=0, target_id="p1")) is True

    def test_cancel_nonexistent_raises(self):
        """意图：取消不存在的点赞 → 抛 NotLikedError。"""
        repo = MockLikeRepository.empty()
        with pytest.raises(NotLikedError):
            repo.cancel(LikeCancel(user_id="u1", target_type=0, target_id="p1"))

    def test_cancel_twice_raises(self):
        """意图：重复取消 → 抛 NotLikedError。"""
        repo = MockLikeRepository.empty()
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        repo.cancel(LikeCancel(user_id="u1", target_type=0, target_id="p1"))
        with pytest.raises(NotLikedError):
            repo.cancel(LikeCancel(user_id="u1", target_type=0, target_id="p1"))

    # ==================== R ====================

    def test_get_likes_by_user(self):
        """意图：按 user_id + target_type 查询用户的点赞列表。"""
        repo = MockLikeRepository.empty()
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p2"))
        repo.create_or_restore(LikeCreate(user_id="u2", target_type=0, target_id="p1"))

        result = repo.get_likes(LikeDto(user_id="u1", target_type=0), page=0, page_size=10)
        assert result.total == 2
        assert result.count == 2

    def test_get_likes_by_target(self):
        """意图：按 target_type + target_id 查询某内容的点赞列表。"""
        repo = MockLikeRepository.empty()
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        repo.create_or_restore(LikeCreate(user_id="u2", target_type=0, target_id="p1"))
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=1, target_id="c1"))

        result = repo.get_likes(LikeDto(target_type=0, target_id="p1"), page=0, page_size=10)
        assert result.total == 2
        assert all(item.target_id == "p1" for item in result.items)

    def test_get_likes_excludes_cancelled(self):
        """意图：已取消的点赞不应出现在查询结果中。"""
        repo = MockLikeRepository.empty()
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p2"))
        repo.cancel(LikeCancel(user_id="u1", target_type=0, target_id="p1"))

        result = repo.get_likes(LikeDto(user_id="u1", target_type=0), page=0, page_size=10)
        assert result.total == 1
        assert result.items[0].target_id == "p2"

    def test_get_likes_all_three_fields(self):
        """意图：三个字段全传 → 查特定记录。"""
        repo = MockLikeRepository.empty()
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id="p1"))
        repo.create_or_restore(LikeCreate(user_id="u1", target_type=1, target_id="c1"))

        result = repo.get_likes(
            LikeDto(user_id="u1", target_type=0, target_id="p1"),
            page=0, page_size=10,
        )
        assert result.total == 1

        result2 = repo.get_likes(
            LikeDto(user_id="u1", target_type=0, target_id="p999"),
            page=0, page_size=10,
        )
        assert result2.total == 0

    def test_get_likes_pagination(self):
        """意图：分页参数正确。"""
        repo = MockLikeRepository.empty()
        for i in range(5):
            repo.create_or_restore(LikeCreate(user_id="u1", target_type=0, target_id=f"p{i}"))

        result = repo.get_likes(LikeDto(user_id="u1", target_type=0), page=0, page_size=2)
        assert result.total == 5
        assert result.count == 2

    def test_get_likes_empty(self):
        """意图：无匹配时返回空列表。"""
        repo = MockLikeRepository.empty()
        result = repo.get_likes(LikeDto(user_id="nonexistent"), page=0, page_size=10)
        assert result.total == 0
        assert result.count == 0
        assert result.items == []
