from datetime import datetime, timezone, timedelta

import pytest

from app.schemas.v2.user import UserCreate
from app.schemas.v2.user_dto import UserInfoDto, UserTimeDto, UserUpdateDto
from app.models.v2.user import UserRole
from app.schemas.v2.user_stats import UserStatsDto

from app.storage.v2.mock.mock_user import MockUserRepository, MockUserStatsRepository


class TestMockUserRepository:
    def test_create_and_find_user_by_uid_should_return_user(self):
        """意图：创建用户后，应能通过 uid 查到同一条用户记录。"""
        repo = MockUserRepository()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))

        found = repo.find_user(uid=user.uid)
        assert found is not None
        assert found.uid == user.uid
        assert found.user_info.username == "u"

    def test_find_user_should_return_none_when_soft_deleted(self):
        """意图：软删除（deleted_at 非空）后，find_user 应返回 None。"""
        repo = MockUserRepository()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))

        now = datetime.now(timezone(timedelta(hours=8)))
        repo.update_user(user.uid, UserUpdateDto(user_data=UserTimeDto(deleted_at=now)))

        assert repo.find_user(uid=user.uid) is None

    def test_update_user_should_apply_user_info_and_password(self):
        """意图：update_user 应能更新 user_info 字段，并同时更新 password 存储。"""
        repo = MockUserRepository()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))

        updated = repo.update_user(
            user.uid,
            UserUpdateDto(
                user_info=UserInfoDto(username="u2", bio="bio", role=UserRole.ADMIN),
                password="new_pw",
            ),
        )
        assert updated is not None
        assert updated.user_info.username == "u2"
        assert updated.user_info.bio == "bio"
        assert updated.user_info.role == UserRole.ADMIN
        assert repo.get_password(user.uid) == "new_pw"

    def test_list_users_should_support_username_filter_and_pagination(self):
        """意图：list_users 支持按 username 过滤，并支持分页返回。"""
        repo = MockUserRepository()
        repo.create_user(UserCreate(username="same", phone="111", password="pw"))
        repo.create_user(UserCreate(username="same", phone="222", password="pw"))
        repo.create_user(UserCreate(username="diff", phone="333", password="pw"))

        res = repo.list_users(username="same", page=0, page_size=10)
        assert res.total == 2
        assert res.count == 2
        assert all(u.user_info.username == "same" for u in res.users)

        res2 = repo.list_users(page=0, page_size=2)
        assert res2.count == 2

    def test_delete_user_should_remove_user_and_password(self):
        """意图：delete_user 应删除用户记录并移除对应 password。"""
        repo = MockUserRepository()
        user = repo.create_user(UserCreate(username="u", phone="111", password="pw"))

        ok = repo.delete_user(user.uid)
        assert ok is True
        assert repo.find_user(uid=user.uid) is None
        assert repo.get_password(user.uid) is None


class TestMockUserStatsRepository:
    def test_get_or_create_stats_should_default_zero(self):
        """意图：get_or_create_stats 在没有记录时创建默认统计（0/0）。"""
        user_repo = MockUserRepository()
        stats_repo = MockUserStatsRepository(user_repo)

        stats = stats_repo.get_or_create_stats("uid")
        assert isinstance(stats, UserStatsDto)
        assert stats.following_count == 0
        assert stats.followers_count == 0

    def test_update_stats_should_increase_and_not_below_zero(self):
        """意图：update_stats 支持增量更新，且计数不应被更新到负数。"""
        user_repo = MockUserRepository()
        stats_repo = MockUserStatsRepository(user_repo)

        stats_repo.get_or_create_stats("uid")
        stats_repo.update_stats("uid", following_step=5, followers_step=10)
        stats = stats_repo.get_by_user_id("uid")
        assert stats is not None
        assert stats.following_count == 5
        assert stats.followers_count == 10

        stats_repo.update_stats("uid", following_step=-100, followers_step=-100)
        stats2 = stats_repo.get_by_user_id("uid")
        assert stats2 is not None
        assert stats2.following_count == 0
        assert stats2.followers_count == 0

    def test_find_stats_with_user_should_return_none_when_user_missing(self):
        """意图：with_user=True 时，如果用户不存在，应返回 None。"""
        user_repo = MockUserRepository()
        stats_repo = MockUserStatsRepository(user_repo)
        stats_repo.get_or_create_stats("uid")

        assert stats_repo.find_stats("uid", with_user=True) is None
