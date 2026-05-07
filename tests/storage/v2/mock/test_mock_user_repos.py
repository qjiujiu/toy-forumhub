import pytest
from datetime import datetime, timezone, timedelta

from tests.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate, UserInfoDto, UserUpdateDto, UserTimeDto
from app.schemas.v2.user_stats import UserStatsDto
from app.models.v2.user import UserRole, UserStatus


class TestMockUserRepository:
    """测试 MockUserRepository（聚合仓储）是否符合 IUserRepository 协议约定。"""

    def test_create_and_find_user_by_uid(self):
        """意图：创建用户后，应能通过 uid 查到同一用户记录。"""
        repo = MockUserRepository.empty()
        user_data = UserCreate(username="u", phone="111", password="pw")
        user = repo.create_user(user_data)
        found = repo.find_user(uid=user.uid)
        assert found is not None
        assert found.uid == user.uid
        assert found.user_info.username == "u"

    def test_find_user_by_phone(self):
        """意图：通过 phone 查询用户。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        found = repo.find_user(phone="111")
        assert found is not None
        assert found.uid == user.uid
        assert repo.find_user(phone="999") is None

    def test_find_user_returns_none_when_soft_deleted(self):
        """意图：软删除（deleted_at 非空）后，find_user 返回 None。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        repo.update_user(user.uid, UserUpdateDto(user_data=UserTimeDto(deleted_at=datetime.now(timezone(timedelta(hours=8))))))
        assert repo.find_user(uid=user.uid) is None

    def test_list_users_with_username_filter(self):
        """意图：list_users 支持按 username 过滤。"""
        repo = MockUserRepository.empty()
        repo.create_user(UserCreate(username="same", phone="111", password="pw"))
        repo.create_user(UserCreate(username="same", phone="222", password="pw"))
        repo.create_user(UserCreate(username="diff", phone="333", password="pw"))
        res = repo.list_users(username="same", page=0, page_size=10)
        assert res.total == 2
        assert res.count == 2
        assert all(u.user_info.username == "same" for u in res.users)

    def test_list_users_pagination(self):
        """意图：list_users 分页返回正确。"""
        repo = MockUserRepository.empty()
        repo.create_user(UserCreate(username="u1", phone="111", password="pw"))
        repo.create_user(UserCreate(username="u2", phone="222", password="pw"))
        repo.create_user(UserCreate(username="u3", phone="333", password="pw"))
        res = repo.list_users(page=0, page_size=2)
        assert res.total == 3
        assert res.count == 2

    def test_update_user_info(self):
        """意图：update_user 遵循 PATCH 语义，只更新显式字段。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        updated = repo.update_user(user.uid, UserUpdateDto(user_info=UserInfoDto(username="u2", bio="bio")))
        assert updated.user_info.username == "u2"
        assert updated.user_info.bio == "bio"
        # role 可通过同一方法更新
        updated2 = repo.update_user(user.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        assert updated2.user_info.role == UserRole.ADMIN

    def test_get_password(self):
        """意图：get_password 返回存储的密码。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        assert repo.get_password(user.uid) == "pw"
        assert repo.get_password("invalid") is None

    def test_delete_user_removes_user_password_and_stats(self):
        """意图：delete_user 应删除用户记录、密码和统计。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        assert repo.delete_user(user.uid) is True
        assert repo.find_user(uid=user.uid) is None
        assert repo.get_password(user.uid) is None
        with pytest.raises(RuntimeError):
            repo.get_stats(user.uid)

    def test_delete_nonexistent_returns_false(self):
        """意图：delete_user 不存在的用户返回 False。"""
        repo = MockUserRepository.empty()
        assert repo.delete_user("nonexistent") is False

    def test_get_stats_exists_after_create(self):
        """意图：create_user 保证用户聚合的统计记录存在（默认 0/0）。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        stats = repo.get_stats(user.uid)
        assert isinstance(stats, UserStatsDto)
        assert stats.following_count == 0
        assert stats.followers_count == 0

    def test_update_stats_increments_and_clamps_below_zero(self):
        """意图：update_stats 支持增量更新，且计数不应被更新到负数。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        repo.update_stats(user.uid, following_step=5, followers_step=10)
        stats = repo.get_stats(user.uid)
        assert stats.following_count == 5
        assert stats.followers_count == 10
        repo.update_stats(user.uid, following_step=-100, followers_step=-100)
        stats2 = repo.get_stats(user.uid)
        assert stats2.following_count == 0
        assert stats2.followers_count == 0

    def test_get_user_profile_returns_none_when_missing(self):
        """意图：用户不存在时，get_user_profile 应返回 None。"""
        repo = MockUserRepository()
        assert repo.get_user_profile("uid") is None

    def test_get_user_profile_returns_user_with_stats(self):
        """意图：用户存在时，get_user_profile 返回 UserOut + UserStatsDto。"""
        repo = MockUserRepository.empty()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))
        profile = repo.get_user_profile(user.uid)
        assert profile is not None
        assert profile.user_info.uid == user.uid
        assert profile.user_stats.following_count == 0
        assert profile.user_stats.followers_count == 0
