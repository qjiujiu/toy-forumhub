from tests.mock.mock_user import MockUserRepository, MockUserStatsRepository
from app.schemas.v2.user import UserDto, UserCreate, UserUpdate, UserPasswordUpdate
from app.models.user import UserRole, UserStatus
from app.service.v2.user_svc import UserService
from app.core.exceptions import UserNotFound, PasswordMismatchError, AdminPermissionDenied
from app.core.security import verify_password
import pytest


@pytest.fixture
def user_repo():
    return MockUserRepository()


@pytest.fixture
def stats_repo(user_repo):
    return MockUserStatsRepository(user_repo)


@pytest.fixture
def user_svc(user_repo, stats_repo):
    return UserService(user_repo, stats_repo)


class TestUserService:
    def test_create_user(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="testuser", phone="1234567890")
        user_data = UserCreate(user_info=userDto, password="plain_password")
        result = user_svc.create_user(user_data, to_dict=False)

        assert result.user_info.username == "testuser"
        assert verify_password("plain_password", user_repo.passwords[result.uid])

        stat = stats_repo.get_by_user_id(result.uid)
        assert stat is not None
        assert stat.following_count == 0
        assert stat.followers_count == 0

    def test_get_batch_users(self, user_svc, user_repo, stats_repo):
        userDto1 = UserDto(username="u1", phone="111")
        userDto2 = UserDto(username="u2", phone="222")
        user_svc.create_user(UserCreate(user_info=userDto1, password="pw"), to_dict=False)
        user_svc.create_user(UserCreate(user_info=userDto2, password="pw"), to_dict=False)

        result = user_svc.get_batch_users(page=0, page_size=10, to_dict=False)
        assert result.total == 2
        assert result.count == 2
        assert len(result.users) == 2

    def test_get_users_by_username(self, user_svc, user_repo, stats_repo):
        userDto1 = UserDto(username="same_name", phone="111")
        userDto2 = UserDto(username="same_name", phone="222")
        userDto3 = UserDto(username="diff_name", phone="333")
        user_svc.create_user(UserCreate(user_info=userDto1, password="pw"), to_dict=False)
        user_svc.create_user(UserCreate(user_info=userDto2, password="pw"), to_dict=False)
        user_svc.create_user(UserCreate(user_info=userDto3, password="pw"), to_dict=False)

        result = user_svc.get_users_by_username("same_name", to_dict=False)
        assert result.total == 2
        assert len(result.users) == 2

    def test_get_user_by_uid(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        result = user_svc.get_user_by_uid(u.uid, to_dict=False)
        assert result is not None
        assert result.uid == u.uid

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid("invalid_uid", to_dict=False)

    def test_get_user_by_phone(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        result = user_svc.get_user_by_phone("111", to_dict=False)
        assert result is not None
        assert result.uid == u.uid

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_phone("999", to_dict=False)

    def test_get_user_profile(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        stats_repo.update_stats(u.uid, following_step=5, followers_step=10)

        result = user_svc.get_user_profile(u.uid, to_dict=False)
        assert result is not None
        assert result.user_info.uid == u.uid
        assert result.user_stats.following_count == 5
        assert result.user_stats.followers_count == 10

        with pytest.raises(UserNotFound):
            user_svc.get_user_profile("invalid", to_dict=False)

    def test_update_user(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        updateDto = UserDto(username="new_u", phone="111", bio="new bio")
        update_data = UserUpdate(user_info=updateDto)
        result = user_svc.update_user(u.uid, update_data, to_dict=False)
        assert result.user_info.username == "new_u"
        assert result.user_info.bio == "new bio"

    def test_change_password(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="old_pw"), to_dict=False)

        pw_update = UserPasswordUpdate(old_password="old_pw", new_password="new_pw")
        res = user_svc.change_password(u.uid, pw_update)
        assert res is True

        assert verify_password("new_pw", user_repo.passwords[u.uid])

        pw_update_wrong = UserPasswordUpdate(old_password="wrong", new_password="new_pw")
        with pytest.raises(PasswordMismatchError):
            user_svc.change_password(u.uid, pw_update_wrong)

    def test_soft_delete_user(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        res = user_svc.soft_delete_user(u.uid)
        assert res is True

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid(u.uid, to_dict=False)

    def test_hard_delete_user(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        adminDto = UserDto(username="admin", phone="999")
        admin = user_svc.create_user(UserCreate(user_info=adminDto, password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, role=2)

        res = user_svc.hard_delete_user(admin.uid, u.uid)
        assert res is True
        assert u.uid not in user_repo.users

    def test_ban_user_by_uid(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        adminDto = UserDto(username="admin", phone="999")
        admin = user_svc.create_user(UserCreate(user_info=adminDto, password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, role=2)

        res = user_svc.ban_user_by_uid(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.status == UserStatus.BANNED.value

    def test_ban_user_without_admin(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        userDto2 = UserDto(username="u2", phone="222")
        u2 = user_svc.create_user(UserCreate(user_info=userDto2, password="pw"), to_dict=False)

        with pytest.raises(AdminPermissionDenied):
            user_svc.ban_user_by_uid(u2.uid, u.uid)

    def test_frozen_user_by_uid(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        adminDto = UserDto(username="admin", phone="999")
        admin = user_svc.create_user(UserCreate(user_info=adminDto, password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, role=2)

        res = user_svc.frozen_user_by_uid(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.status == UserStatus.FROZEN.value

    def test_user_to_admin(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        adminDto = UserDto(username="admin", phone="999")
        admin = user_svc.create_user(UserCreate(user_info=adminDto, password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, role=2)

        res = user_svc.user_to_admin(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.role == UserRole.ADMIN.value

    def test_user_to_moderator(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="pw"), to_dict=False)

        adminDto = UserDto(username="admin", phone="999")
        admin = user_svc.create_user(UserCreate(user_info=adminDto, password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, role=2)

        res = user_svc.user_to_moderator(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.role == UserRole.MODERATOR.value

    def test_get_password(self, user_svc, user_repo, stats_repo):
        userDto = UserDto(username="u", phone="111")
        u = user_svc.create_user(UserCreate(user_info=userDto, password="old_pw"), to_dict=False)

        password = user_repo.get_password(u.uid)
        assert password is not None

    def test_update_user_not_found(self, user_svc, user_repo, stats_repo):
        updateDto = UserDto(username="new_u", phone="111", bio="new bio")
        update_data = UserUpdate(user_info=updateDto)

        result = user_svc.update_user("invalid_uid", update_data, to_dict=False)
        assert result is None