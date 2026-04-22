from tests.mock.mock_user import MockUserRepository, MockUserStatsRepository
from app.schemas.user import (
    UserCreate, UserUpdate, AdminUserUpdate, UserPasswordUpdate
)
from app.models.user import UserRole, UserStatus
from app.service import user_svc
from app.core.exceptions import UserNotFound, PasswordMismatchError
from app.core.security import verify_password
import pytest


@pytest.fixture
def user_repo():
    return MockUserRepository()


@pytest.fixture
def stats_repo(user_repo):
    return MockUserStatsRepository(user_repo)


class TestUserService:
    def test_create_user(self, user_repo, stats_repo):
        user_data = UserCreate(
            username="testuser",
            phone="1234567890",
            password="plain_password"
        )
        result = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        # 这个就是断言
        assert result.username == "testuser"
        assert verify_password("plain_password", user_repo.users[result.uid].password)

        # check stats initialized
        stat = stats_repo.get_by_user_id(result.uid)
        assert stat is not None
        assert stat.following_count == 0
        assert stat.followers_count == 0

    def test_get_batch_users(self, user_repo, stats_repo):
        user_data1 = UserCreate(username="u1", phone="111", password="pw")
        user_data2 = UserCreate(username="u2", phone="222", password="pw")
        user_svc.create_user(user_repo, stats_repo, user_data1, to_dict=False)
        user_svc.create_user(user_repo, stats_repo, user_data2, to_dict=False)

        result = user_svc.get_batch_users(user_repo, page=0, page_size=10, to_dict=False)
        assert result.total == 2
        assert result.count == 2
        assert len(result.users) == 2

    def test_get_users_by_username(self, user_repo, stats_repo):
        user_data1 = UserCreate(username="same_name", phone="111", password="pw")
        user_data2 = UserCreate(username="same_name", phone="222", password="pw")
        user_data3 = UserCreate(username="diff_name", phone="333", password="pw")
        user_svc.create_user(user_repo, stats_repo, user_data1, to_dict=False)
        user_svc.create_user(user_repo, stats_repo, user_data2, to_dict=False)
        user_svc.create_user(user_repo, stats_repo, user_data3, to_dict=False)

        result = user_svc.get_users_by_username(user_repo, "same_name", to_dict=False)
        assert result.total == 2
        assert len(result.users) == 2

    def test_get_user_by_uid(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        result = user_svc.get_user_by_uid(user_repo, u.uid, to_dict=False)
        assert result is not None
        assert result.uid == u.uid

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid(user_repo, "invalid_uid", to_dict=False)

    def test_get_user_profile(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        # modify stat
        stats_repo.update_following(u.uid, 5)
        stats_repo.update_followers(u.uid, 10)

        result = user_svc.get_user_profile(stats_repo, u.uid, to_dict=False)
        assert result is not None
        assert result.user.uid == u.uid
        assert result.following_count == 5
        assert result.followers_count == 10

        result_invalid = user_svc.get_user_profile(stats_repo, "invalid", to_dict=False)
        assert isinstance(result_invalid, UserNotFound)

    def test_update_user(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        update_data = UserUpdate(username="new_u", bio="new bio")
        result = user_svc.update_user(user_repo, u.uid, update_data, to_dict=False)
        assert result.username == "new_u"
        assert result.bio == "new bio"

        u2 = user_repo.get_user_by_uid(u.uid)
        assert u2.username == "new_u"

    def test_admin_update_user(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        admin_data = AdminUserUpdate(role=UserRole.ADMIN, status=UserStatus.BANNED)
        result = user_svc.admin_update_user(user_repo, u.uid, admin_data, to_dict=False)
        assert result.role == UserRole.ADMIN
        assert result.status == UserStatus.BANNED

    def test_change_password(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="old_pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        pw_update = UserPasswordUpdate(old_password="old_pw", new_password="new_pw")
        res = user_svc.change_password(user_repo, u.uid, pw_update)
        assert res is True

        u2 = user_repo.users[u.uid]
        assert verify_password("new_pw", u2.password)

        pw_update_wrong = UserPasswordUpdate(old_password="wrong", new_password="new_pw")
        with pytest.raises(PasswordMismatchError):
            user_svc.change_password(user_repo, u.uid, pw_update_wrong)

    def test_soft_delete_user(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        res = user_svc.soft_delete_user(user_repo, u.uid)
        assert res is True

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid(user_repo, u.uid, to_dict=False)

        u_all = user_repo.users[u.uid]
        assert u_all.deleted_at is not None

    def test_hard_delete_user(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        res = user_svc.hard_delete_user(user_repo, u.uid)
        assert res is True
        assert u.uid not in user_repo.users

    def test_admin_get_users(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)

        res = user_svc.admin_get_users(user_repo, page=0, page_size=10, to_dict=False)
        assert res.total == 1

    def test_admin_get_user_by_uid(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)
        user_svc.soft_delete_user(user_repo, u.uid)

        res = user_svc.admin_get_user_by_uid(user_repo, u.uid, to_dict=False)
        assert res is not None
        assert res.uid == u.uid
        assert res.deleted_at is not None

    def test_admin_get_users_by_username(self, user_repo, stats_repo):
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(user_repo, stats_repo, user_data, to_dict=False)
        user_svc.soft_delete_user(user_repo, u.uid)

        res = user_svc.admin_get_users_by_username(user_repo, "u", to_dict=False)
        assert res.total == 1

    def test_admin_list_deleted_users(self, user_repo, stats_repo):
        user_data1 = UserCreate(username="u1", phone="111", password="pw")
        u1 = user_svc.create_user(user_repo, stats_repo, user_data1, to_dict=False)

        user_data2 = UserCreate(username="u2", phone="222", password="pw")
        u2 = user_svc.create_user(user_repo, stats_repo, user_data2, to_dict=False)
        user_svc.soft_delete_user(user_repo, u2.uid)

        res = user_svc.admin_list_deleted_users(user_repo, to_dict=False)
        assert res.total == 1
        assert res.users[0].uid == u2.uid

    def test_admin_list_abnormal_status_users(self, user_repo, stats_repo):
        user_data1 = UserCreate(username="u1", phone="111", password="pw")
        user_svc.create_user(user_repo, stats_repo, user_data1, to_dict=False)

        user_data2 = UserCreate(username="u2", phone="222", password="pw", status=UserStatus.BANNED)
        u2 = user_svc.create_user(user_repo, stats_repo, user_data2, to_dict=False)

        res = user_svc.admin_list_abnormal_status_users(user_repo, to_dict=False)
        assert res.total == 1
        assert res.users[0].uid == u2.uid