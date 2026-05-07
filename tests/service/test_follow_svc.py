import pytest

from tests.mock.mock_follow import MockFollowRepository
from tests.mock.mock_user import MockUserRepository

from app.schemas.v2.follow import FollowCreate, FollowCancel
from app.schemas.v2.user import UserCreate
from app.service.v2.follow_svc import FollowService

from app.schemas.v2.user import UserInfoDto, UserUpdateDto
from app.models.v2.user import UserRole

from app.core.exceptions import (
    AlreadyFollowingError,
    FollowYourselfError,
    NotFollowingError,
    UserNotFound,
    AdminPermissionDenied,
)


@pytest.fixture
def user_repo():
    return MockUserRepository.empty()


@pytest.fixture
def follow_repo(user_repo):
    return MockFollowRepository.empty(user_repo=user_repo)


@pytest.fixture
def follow_svc(follow_repo, user_repo):
    return FollowService(follow_repo, user_repo)


class TestFollowService:
    """测试 FollowService 业务逻辑层。"""

    # ==================== follow() ====================

    def test_follow_success(self, follow_svc, user_repo):
        """意图：关注成功，双方的计数更新。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        result = follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        assert result is True
        assert user_repo.get_stats(u1.uid).following_count == 1
        assert user_repo.get_stats(u2.uid).followers_count == 1

    def test_follow_self_raises(self, follow_svc, user_repo):
        """意图：不能关注自己 → FollowYourselfError。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        with pytest.raises(FollowYourselfError):
            follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u1.uid))

    def test_follow_nonexistent_follower_raises(self, follow_svc, user_repo):
        """意图：关注者不存在 → UserNotFound。"""
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        with pytest.raises(UserNotFound):
            follow_svc.follow(FollowCreate(user_id="invalid", followed_user_id=u2.uid))

    def test_follow_nonexistent_target_raises(self, follow_svc, user_repo):
        """意图：被关注者不存在 → UserNotFound。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        with pytest.raises(UserNotFound):
            follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id="invalid"))

    def test_follow_duplicate_raises(self, follow_svc, user_repo):
        """意图：重复关注 → AlreadyFollowingError。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        with pytest.raises(AlreadyFollowingError):
            follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))

    def test_follow_then_unfollow_then_follow_again(self, follow_svc, user_repo):
        """意图：关注→取消→再关注，计数最终为 1。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        follow_svc.unfollow(FollowCancel(user_id=u1.uid, followed_user_id=u2.uid))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        assert user_repo.get_stats(u1.uid).following_count == 1
        assert user_repo.get_stats(u2.uid).followers_count == 1

    # ==================== unfollow() ====================

    def test_unfollow_success(self, follow_svc, user_repo):
        """意图：取消关注成功，计数减一。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        result = follow_svc.unfollow(FollowCancel(user_id=u1.uid, followed_user_id=u2.uid))
        assert result is True
        assert user_repo.get_stats(u1.uid).following_count == 0
        assert user_repo.get_stats(u2.uid).followers_count == 0

    def test_unfollow_nonexistent_raises(self, follow_svc, user_repo):
        """意图：取消不存在的关注 → NotFollowingError。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        with pytest.raises(NotFollowingError):
            follow_svc.unfollow(FollowCancel(user_id=u1.uid, followed_user_id=u2.uid))

    def test_unfollow_twice_raises(self, follow_svc, user_repo):
        """意图：重复取消 → NotFollowingError。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        follow_svc.unfollow(FollowCancel(user_id=u1.uid, followed_user_id=u2.uid))
        with pytest.raises(NotFollowingError):
            follow_svc.unfollow(FollowCancel(user_id=u1.uid, followed_user_id=u2.uid))

    # ==================== hard_unfollow() ====================

    def test_hard_unfollow_success(self, follow_svc, user_repo):
        """意图：硬删除成功，计数减一。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        admin = user_repo.create_user(UserCreate(username="admin", phone="999", password="pw"))
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        result = follow_svc.hard_unfollow(admin.uid, FollowCancel(user_id=u1.uid, followed_user_id=u2.uid))
        assert result is True
        assert user_repo.get_stats(u1.uid).following_count == 0

    def test_hard_unfollow_non_admin_raises(self, follow_svc, user_repo):
        """意图：非管理员硬删除 → AdminPermissionDenied。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        with pytest.raises(AdminPermissionDenied):
            follow_svc.hard_unfollow(u1.uid, FollowCancel(user_id=u1.uid, followed_user_id=u2.uid))

    # ==================== get_followings() / get_followers() ====================

    def test_get_followings(self, follow_svc, user_repo):
        """意图：获取关注列表。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        result = follow_svc.get_followings(user_id=u1.uid, to_dict=False)
        assert result.total == 1
        assert result.items[0].user.uid == u2.uid

    def test_get_followers(self, follow_svc, user_repo):
        """意图：获取粉丝列表。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        u2 = user_repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        follow_svc.follow(FollowCreate(user_id=u1.uid, followed_user_id=u2.uid))
        result = follow_svc.get_followers(user_id=u2.uid, to_dict=False)
        assert result.total == 1
        assert result.items[0].user.uid == u1.uid

    def test_get_followings_empty(self, follow_svc, user_repo):
        """意图：无关注返回空。"""
        u1 = user_repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        result = follow_svc.get_followings(user_id=u1.uid, to_dict=False)
        assert result.total == 0
