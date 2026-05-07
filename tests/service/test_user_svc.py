import pytest

from tests.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate, UserUpdate, UserPasswordUpdate, UserInfoDto, UserUpdateDto
from app.models.v2.user import UserRole, UserStatus
from app.service.v2.user_svc import UserService
from app.core.exceptions import UserNotFound, PasswordMismatchError, AdminPermissionDenied
from app.core.security import verify_password


@pytest.fixture
def user_repo():
    return MockUserRepository.empty()


@pytest.fixture
def user_svc(user_repo):
    return UserService(user_repo)


class TestUserService:
    """测试 UserService 业务逻辑层（基于聚合仓储 + Mock）。"""

    def test_create_user(self, user_svc, user_repo):
        """意图：注册时 service 负责密码 hash，并保证用户统计信息被初始化为 0/0。"""
        result = user_svc.create_user(
            UserCreate(username="testuser", phone="1234567890", password="plain_password"),
            to_dict=False,
        )
        assert result.user_info.username == "testuser"
        assert verify_password("plain_password", user_repo.passwords[result.uid])
        stats = user_repo.get_stats(result.uid)
        assert stats.following_count == 0
        assert stats.followers_count == 0

    def test_get_batch_users(self, user_svc, user_repo):
        """意图：分页查询用户列表时，total/count/users 长度一致且符合分页参数。"""
        user_svc.create_user(UserCreate(username="u1", phone="111", password="pw"), to_dict=False)
        user_svc.create_user(UserCreate(username="u2", phone="222", password="pw"), to_dict=False)
        result = user_svc.get_batch_users(page=0, page_size=10, to_dict=False)
        assert result.total == 2
        assert result.count == 2
        assert len(result.users) == 2

    def test_get_users_by_username(self, user_svc, user_repo):
        """意图：按 username 过滤用户列表时，只返回匹配用户名的用户。"""
        user_svc.create_user(UserCreate(username="same_name", phone="111", password="pw"), to_dict=False)
        user_svc.create_user(UserCreate(username="same_name", phone="222", password="pw"), to_dict=False)
        user_svc.create_user(UserCreate(username="diff_name", phone="333", password="pw"), to_dict=False)
        result = user_svc.get_users_by_username("same_name", to_dict=False)
        assert result.total == 2
        assert len(result.users) == 2

    def test_get_user_by_uid(self, user_svc, user_repo):
        """意图：存在用户返回成功；不存在应抛 UserNotFound。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        result = user_svc.get_user_by_uid(u.uid, to_dict=False)
        assert result is not None
        assert result.uid == u.uid
        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid("invalid_uid")

    def test_get_user_by_phone(self, user_svc, user_repo):
        """意图：根据 phone 查询存在用户应成功；不存在应抛 UserNotFound。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        result = user_svc.get_user_by_phone("111", to_dict=False)
        assert result is not None
        assert result.uid == u.uid
        with pytest.raises(UserNotFound):
            user_svc.get_user_by_phone("999")

    def test_get_user_profile(self, user_svc, user_repo):
        """意图：获取用户 profile 时，应返回聚合后的统计信息；不存在 uid 应抛 UserNotFound。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        user_repo.update_stats(u.uid, following_step=5, followers_step=10)
        result = user_svc.get_user_profile(u.uid, to_dict=False)
        assert result is not None
        assert result.user_info.uid == u.uid
        assert result.user_stats.following_count == 5
        assert result.user_stats.followers_count == 10
        with pytest.raises(UserNotFound):
            user_svc.get_user_profile("invalid")

    def test_update_user(self, user_svc, user_repo):
        """意图：更新用户资料应遵循 PATCH 语义，只更新显式字段。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        update_dto = UserUpdateDto(user_info=UserInfoDto(username="new_u", bio="new bio"))
        result = user_svc.update_user(u.uid, update_dto, to_dict=False)
        assert result.user_info.username == "new_u"
        assert result.user_info.bio == "new bio"

    def test_change_password(self, user_svc, user_repo):
        """意图：修改密码时 old_password 校验成功则更新；失败应抛 PasswordMismatchError。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="old_pw"), to_dict=False)
        pw_update = UserPasswordUpdate(old_password="old_pw", new_password="new_pw")
        res = user_svc.change_password(u.uid, pw_update)
        assert res is True
        assert verify_password("new_pw", user_repo.passwords[u.uid])
        pw_update_wrong = UserPasswordUpdate(old_password="wrong", new_password="new_pw")
        with pytest.raises(PasswordMismatchError):
            user_svc.change_password(u.uid, pw_update_wrong)

    def test_soft_delete_user(self, user_svc, user_repo):
        """意图：软删除后用户应在读路径不可见（get_user_by_uid 抛 UserNotFound）。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        res = user_svc.soft_delete_user(u.uid)
        assert res is True
        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid(u.uid)

    def test_hard_delete_user(self, user_svc, user_repo):
        """意图：硬删除需要管理员权限；成功后用户应从仓库中移除。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        admin = user_svc.create_user(UserCreate(username="admin", phone="999", password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        res = user_svc.hard_delete_user(admin.uid, u.uid)
        assert res is True
        assert u.uid not in user_repo.users

    def test_ban_user_by_uid(self, user_svc, user_repo):
        """意图：管理员封禁用户后，用户状态应变为 BANNED。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        admin = user_svc.create_user(UserCreate(username="admin", phone="999", password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        res = user_svc.ban_user_by_uid(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.user_info.status == UserStatus.BANNED

    def test_ban_user_without_admin(self, user_svc, user_repo):
        """意图：非管理员尝试封禁用户应抛 AdminPermissionDenied。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        u2 = user_svc.create_user(UserCreate(username="u2", phone="222", password="pw"), to_dict=False)
        with pytest.raises(AdminPermissionDenied):
            user_svc.ban_user_by_uid(u2.uid, u.uid)

    def test_frozen_user_by_uid(self, user_svc, user_repo):
        """意图：管理员冻结用户后，用户状态应变为 FROZEN。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        admin = user_svc.create_user(UserCreate(username="admin", phone="999", password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        res = user_svc.frozen_user_by_uid(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.user_info.status == UserStatus.FROZEN

    def test_user_to_admin(self, user_svc, user_repo):
        """意图：管理员提升用户为 ADMIN 时，目标用户角色应变更为 ADMIN。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        admin = user_svc.create_user(UserCreate(username="admin", phone="999", password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        res = user_svc.user_to_admin(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.user_info.role == UserRole.ADMIN

    def test_user_to_moderator(self, user_svc, user_repo):
        """意图：管理员提升用户为 MODERATOR 时，目标用户角色应变更为 MODERATOR。"""
        u = user_svc.create_user(UserCreate(username="u", phone="111", password="pw"), to_dict=False)
        admin = user_svc.create_user(UserCreate(username="admin", phone="999", password="admin_pw"), to_dict=False)
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        res = user_svc.user_to_moderator(admin.uid, u.uid, to_dict=False)
        assert res is not None
        assert res.user_info.role == UserRole.MODERATOR

    def test_update_user_not_found(self, user_svc, user_repo):
        """意图：更新不存在用户时返回 None。"""
        update_dto = UserUpdateDto(user_info=UserInfoDto(username="new_u", bio="new bio"))
        result = user_svc.update_user("invalid_uid", update_dto, to_dict=False)
        assert result is None
