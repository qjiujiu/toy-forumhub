import pytest

from tests.mock.mock_follow import MockFollowRepository
from app.schemas.v2.follow import FollowCreate, FollowCancel, FollowDto
from app.core.exceptions import AlreadyFollowingError, NotFollowingError


class TestMockFollowRepository:
    """测试 MockFollowRepository 是否符合 IFollowRepository 协议约定。"""

    # ==================== C ====================

    def test_follow_new(self):
        """意图：关注一个新用户，返回 True。"""
        repo = MockFollowRepository.empty()
        assert repo.follow(FollowCreate(user_id="u1", followed_user_id="u2")) is True

    def test_follow_duplicate_raises(self):
        """意图：重复关注同一用户 → AlreadyFollowingError。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        with pytest.raises(AlreadyFollowingError):
            repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))

    def test_follow_restore_after_unfollow(self):
        """意图：先取消关注再关注 → 恢复成功。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        repo.unfollow(FollowCancel(user_id="u1", followed_user_id="u2"))
        assert repo.follow(FollowCreate(user_id="u1", followed_user_id="u2")) is True

    # ==================== D ====================

    def test_unfollow_existing(self):
        """意图：取消已存在的关注 → True。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        assert repo.unfollow(FollowCancel(user_id="u1", followed_user_id="u2")) is True

    def test_unfollow_nonexistent_raises(self):
        """意图：取消不存在的关注 → NotFollowingError。"""
        repo = MockFollowRepository.empty()
        with pytest.raises(NotFollowingError):
            repo.unfollow(FollowCancel(user_id="u1", followed_user_id="u2"))

    def test_unfollow_twice_raises(self):
        """意图：重复取消关注 → NotFollowingError。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        repo.unfollow(FollowCancel(user_id="u1", followed_user_id="u2"))
        with pytest.raises(NotFollowingError):
            repo.unfollow(FollowCancel(user_id="u1", followed_user_id="u2"))

    def test_hard_unfollow_existing(self):
        """意图：硬删除存在的关注 → True。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        assert repo.hard_unfollow(FollowCancel(user_id="u1", followed_user_id="u2")) is True

    def test_hard_unfollow_nonexistent_raises(self):
        """意图：硬删除不存在的关注 → NotFollowingError。"""
        repo = MockFollowRepository.empty()
        with pytest.raises(NotFollowingError):
            repo.hard_unfollow(FollowCancel(user_id="u1", followed_user_id="u2"))

    # ==================== R ====================

    def test_get_followings(self):
        """意图：按 user_id 查关注列表。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u3"))
        result = repo.get_follows(FollowDto(user_id="u1"), page=0, page_size=10)
        assert result.total == 2
        assert all(
            item.user.uid in ("u2", "u3") for item in result.items
        )

    def test_get_followers(self):
        """意图：按 followed_user_id 查粉丝列表。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u3"))
        repo.follow(FollowCreate(user_id="u2", followed_user_id="u3"))
        result = repo.get_follows(FollowDto(followed_user_id="u3"), page=0, page_size=10)
        assert result.total == 2
        assert all(
            item.user.uid in ("u1", "u2") for item in result.items
        )

    def test_get_follows_excludes_unfollowed(self):
        """意图：已取消的关注不出现。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u3"))
        repo.unfollow(FollowCancel(user_id="u1", followed_user_id="u2"))
        result = repo.get_follows(FollowDto(user_id="u1"), page=0, page_size=10)
        assert result.total == 1
        assert result.items[0].user.uid == "u3"

    def test_get_follows_mutual_detection(self):
        """意图：互关检测（is_mutual）。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        repo.follow(FollowCreate(user_id="u2", followed_user_id="u1"))
        result = repo.get_follows(FollowDto(user_id="u1"), page=0, page_size=10)
        assert result.total == 1
        assert result.items[0].is_mutual is True

    def test_get_follows_not_mutual(self):
        """意图：单向关注 is_mutual=False。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        result = repo.get_follows(FollowDto(user_id="u1"), page=0, page_size=10)
        assert result.total == 1
        assert result.items[0].is_mutual is False

    def test_get_follows_mutual_after_unfollow_breaks(self):
        """意图：取消互关后 is_mutual 变为 False。"""
        repo = MockFollowRepository.empty()
        repo.follow(FollowCreate(user_id="u1", followed_user_id="u2"))
        repo.follow(FollowCreate(user_id="u2", followed_user_id="u1"))
        repo.unfollow(FollowCancel(user_id="u2", followed_user_id="u1"))
        result = repo.get_follows(FollowDto(user_id="u1"), page=0, page_size=10)
        assert result.items[0].is_mutual is False

    def test_get_follows_pagination(self):
        """意图：分页正确。"""
        repo = MockFollowRepository.empty()
        for i in range(5):
            repo.follow(FollowCreate(user_id="u1", followed_user_id=f"u{i}"))
        result = repo.get_follows(FollowDto(user_id="u1"), page=0, page_size=2)
        assert result.total == 5
        assert result.count == 2

    def test_get_follows_empty(self):
        """意图：无关注时返回空。"""
        repo = MockFollowRepository.empty()
        result = repo.get_follows(FollowDto(user_id="u1"), page=0, page_size=10)
        assert result.total == 0
        assert result.items == []
