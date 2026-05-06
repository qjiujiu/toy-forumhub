from app.schemas.v2.user import UserCreate, UserInfoUpdateDto
from app.schemas.v2.user_req import UserAdminPatch, UserInfoPatch, UserPasswordPatch
from app.schemas.v2.user_stats import UserStatsDto
from app.storage.v2.mock.mock_user import MockUserRepository
from app.models.v2.user import UserRole
from datetime import datetime, timezone, timedelta
import pytest

class TestMockUserRepository:
    def test_create_and_find_user_by_uid_should_return_user(self):
        """意图：创建用户后，应能通过 uid 查到同一条用户记录。"""
        repo = MockUserRepository.empty()
        user_data = UserCreate(username="u", phone="111", password="pw")
        user = repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        found = repo.find_user(uid=user.uid)
        assert found is not None
        assert found.uid == user.uid
        assert found.user_info.username == "u"

    def test_find_user_should_return_none_when_soft_deleted(self):
        """意图：软删除（deleted_at 非空）后，find_user 应返回 None。"""
        repo = MockUserRepository.empty()
        user_data = UserCreate(username="u", phone="111", password="pw")
        user = repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        assert repo.update_user(user.uid, UserAdminPatch(deleted_at=datetime.now(timezone(timedelta(hours=8))))) is not None

        assert repo.find_user(uid=user.uid) is None

    def test_update_user_info_and_reset_password_should_work(self):
        """意图：方向A拆分接口后，信息更新与密码重置都应可用且语义清晰。"""
        repo = MockUserRepository.empty()
        user_data = UserCreate(username="u", phone="111", password="pw")
        user = repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        updated = repo.update_user(user.uid, UserInfoPatch(username="u2", bio="bio"))
        assert updated is not None
        assert updated.user_info.username == "u2"
        assert updated.user_info.bio == "bio"

        # role 只能通过管理员方法 set_role 更新（避免普通更新越权）
        updated2 = repo.update_user(user.uid, UserAdminPatch(role=UserRole.ADMIN))
        assert updated2 is not None
        assert updated2.user_info.role == UserRole.ADMIN

        assert repo.update_user(user.uid, UserPasswordPatch(password="new_pw")) is not None
        assert repo.get_password(user.uid) == "new_pw"

    def test_list_users_should_support_username_filter_and_pagination(self):
        """意图：list_users 支持按 username 过滤，并支持分页返回。"""
        repo = MockUserRepository.empty()
        u1 = UserCreate(username="same", phone="111", password="pw")
        u2 = UserCreate(username="same", phone="222", password="pw")
        u3 = UserCreate(username="diff", phone="333", password="pw")
        repo.create_user(username=u1.username, phone=u1.phone, hashed_password=u1.password)
        repo.create_user(username=u2.username, phone=u2.phone, hashed_password=u2.password)
        repo.create_user(username=u3.username, phone=u3.phone, hashed_password=u3.password)

        res = repo.list_users(username="same", page=0, page_size=10)
        assert res.total == 2
        assert res.count == 2
        assert all(u.user_info.username == "same" for u in res.users)

        res2 = repo.list_users(page=0, page_size=2)
        assert res2.count == 2

    def test_delete_user_should_remove_user_and_password(self):
        """意图：delete_user 应删除用户记录并移除对应 password。"""
        repo = MockUserRepository.empty()
        user_data = UserCreate(username="u", phone="111", password="pw")
        user = repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        ok = repo.delete_user(user.uid)
        assert ok is True
        assert repo.find_user(uid=user.uid) is None
        assert repo.get_password(user.uid) is None


class TestMockUserStatsAggregate:
    def test_get_stats_should_exist_after_create_user(self):
        """意图：创建用户后，user_stats 应作为聚合不变量存在（默认 0/0）。"""
        repo = MockUserRepository.empty()
        user_data = UserCreate(username="u", phone="111", password="pw")
        user = repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        stats = repo.get_stats(user.uid)
        assert isinstance(stats, UserStatsDto)
        assert stats.following_count == 0
        assert stats.followers_count == 0

    def test_update_stats_should_increase_and_not_below_zero(self):
        """意图：聚合仓储的 update_stats 支持增量更新，且计数不应被更新到负数。"""
        repo = MockUserRepository.empty()

        user_data = UserCreate(username="u", phone="111", password="pw")
        user = repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)
        repo.update_stats(user.uid, following_step=5, followers_step=10)
        stats = repo.get_stats(user.uid)
        assert stats.following_count == 5
        assert stats.followers_count == 10

        repo.update_stats(user.uid, following_step=-100, followers_step=-100)
        stats2 = repo.get_stats(user.uid)
        assert stats2.following_count == 0
        assert stats2.followers_count == 0

    def test_get_user_profile_should_return_none_when_user_missing(self):
        """意图：用户不存在时，get_user_profile 应返回 None。"""
        repo = MockUserRepository()
        assert repo.get_user_profile("uid") is None
