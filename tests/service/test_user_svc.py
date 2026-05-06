from app.storage.v2.mock.mock_user import MockUserRepository
from app.schemas.v2.user import (
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserInfoUpdateDto,
)
from app.schemas.v2.user_req import UserAdminPatch
from app.models.v2.user import UserRole, UserStatus
from app.service.v2.user_svc import UserService
from app.core.exceptions import UserNotFound, PasswordMismatchError, AdminPermissionDenied
from app.core.security import verify_password
import pytest


@pytest.fixture
def user_repo():
    # service 单测默认使用“干净仓库”，避免被预置数据干扰断言
    return MockUserRepository.empty()


@pytest.fixture
def user_svc(user_repo):
    return UserService(user_repo)


class TestUserService:
    def test_create_user(self, user_svc, user_repo):
        """测试意图：注册创建用户时，service 负责密码 hash，并保证用户聚合的统计信息被初始化为 0/0。"""
        user_data = UserCreate(username="testuser", phone="1234567890", password="plain_password")
        result = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        assert result.user_info.username == "testuser"
        assert verify_password("plain_password", user_repo.passwords[result.uid])

        # 统计信息属于“用户聚合”的一部分：
        # - 物理上 user_stats 是单独表
        # - 但业务层通过 user_repo/user_svc 即可访问，不应再依赖单独的 stats_repo
        profile = user_svc.get_user_profile(result.uid)
        assert profile.user_stats.following_count == 0
        assert profile.user_stats.followers_count == 0

    def test_get_batch_users(self, user_svc, user_repo):
        """测试意图：分页查询用户列表时，返回 total/count/users 长度应一致且符合分页参数。"""
        user_data1 = UserCreate(username="u1", phone="111", password="pw")
        user_data2 = UserCreate(username="u2", phone="222", password="pw")
        user_svc.create_user(username=user_data1.username, phone=user_data1.phone, password=user_data1.password)
        user_svc.create_user(username=user_data2.username, phone=user_data2.phone, password=user_data2.password)

        result = user_svc.get_batch_users(page=0, page_size=10)
        assert result.total == 2
        assert result.count == 2
        assert len(result.users) == 2

    def test_get_users_by_username(self, user_svc, user_repo):
        """测试意图：按 username 过滤用户列表时，只返回匹配用户名的用户集合（数量正确）。"""
        user_data1 = UserCreate(username="same_name", phone="111", password="pw")
        user_data2 = UserCreate(username="same_name", phone="222", password="pw")
        user_data3 = UserCreate(username="diff_name", phone="333", password="pw")
        user_svc.create_user(username=user_data1.username, phone=user_data1.phone, password=user_data1.password)
        user_svc.create_user(username=user_data2.username, phone=user_data2.phone, password=user_data2.password)
        user_svc.create_user(username=user_data3.username, phone=user_data3.phone, password=user_data3.password)

        result = user_svc.get_users_by_username("same_name")
        assert result.total == 2
        assert len(result.users) == 2

    def test_get_user_by_uid(self, user_svc, user_repo):
        """测试意图：根据 uid 查询存在用户应成功；查询不存在用户应抛出 UserNotFound。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        result = user_svc.get_user_by_uid(u.uid)
        assert result is not None
        assert result.uid == u.uid

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid("invalid_uid")

    def test_get_user_by_phone(self, user_svc, user_repo):
        """测试意图：根据 phone 查询存在用户应成功；查询不存在 phone 应抛出 UserNotFound。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        result = user_svc.get_user_by_phone("111")
        assert result is not None
        assert result.uid == u.uid

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_phone("999")

    def test_get_user_profile(self, user_svc, user_repo):
        """测试意图：获取用户 profile（UserOut + Stats）时，应返回聚合后的统计信息；不存在 uid 应抛 UserNotFound。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        # 通过聚合仓储更新统计信息
        user_repo.update_stats(u.uid, following_step=5, followers_step=10)

        result = user_svc.get_user_profile(u.uid)
        assert result is not None
        assert result.user_info.uid == u.uid
        assert result.user_stats.following_count == 5
        assert result.user_stats.followers_count == 10

        with pytest.raises(UserNotFound):
            user_svc.get_user_profile("invalid")

    def test_update_user(self, user_svc, user_repo):
        """测试意图：普通用户更新资料应遵循 PATCH 语义（只更新显式字段），并返回更新后的用户信息。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        update_body = UserUpdate(user_info=UserInfoUpdateDto(username="new_u", bio="new bio"))
        result = user_svc.update_user(u.uid, update_body)
        assert result.user_info.username == "new_u"
        assert result.user_info.bio == "new bio"

    def test_change_password(self, user_svc, user_repo):
        """测试意图：修改密码时 old_password 校验成功则更新为新密码；校验失败应抛 PasswordMismatchError。"""
        user_data = UserCreate(username="u", phone="111", password="old_pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        pw_update = UserPasswordUpdate(old_password="old_pw", new_password="new_pw")
        res = user_svc.change_password(u.uid, pw_update)
        assert res is True

        assert verify_password("new_pw", user_repo.passwords[u.uid])

        pw_update_wrong = UserPasswordUpdate(old_password="wrong", new_password="new_pw")
        with pytest.raises(PasswordMismatchError):
            user_svc.change_password(u.uid, pw_update_wrong)

    def test_soft_delete_user(self, user_svc, user_repo):
        """测试意图：软删除用户后，用户应在读路径不可见（get_user_by_uid 抛 UserNotFound）。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        res = user_svc.soft_delete_user(u.uid)
        assert res is True

        with pytest.raises(UserNotFound):
            user_svc.get_user_by_uid(u.uid)

    def test_hard_delete_user(self, user_svc, user_repo):
        """测试意图：硬删除需要管理员权限；成功后用户应从仓库中移除。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        admin_data = UserCreate(username="admin", phone="999", password="admin_pw")
        admin = user_svc.create_user(username=admin_data.username, phone=admin_data.phone, password=admin_data.password)
        user_repo.update_user(admin.uid, UserAdminPatch(role=UserRole.ADMIN))

        res = user_svc.hard_delete_user(admin.uid, u.uid)
        assert res is True
        assert u.uid not in user_repo.users

    def test_ban_user_by_uid(self, user_svc, user_repo):
        """测试意图：管理员封禁用户后，用户状态应变为 BANNED。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        admin_data = UserCreate(username="admin", phone="999", password="admin_pw")
        admin = user_svc.create_user(username=admin_data.username, phone=admin_data.phone, password=admin_data.password)
        user_repo.update_user(admin.uid, UserAdminPatch(role=UserRole.ADMIN))

        res = user_svc.ban_user_by_uid(admin.uid, u.uid)
        assert res is not None
        assert res.user_info.status == UserStatus.BANNED

    def test_ban_user_without_admin(self, user_svc, user_repo):
        """测试意图：非管理员尝试封禁用户应被拒绝，并抛 AdminPermissionDenied。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        user_data2 = UserCreate(username="u2", phone="222", password="pw")
        u2 = user_svc.create_user(username=user_data2.username, phone=user_data2.phone, password=user_data2.password)

        with pytest.raises(AdminPermissionDenied):
            user_svc.ban_user_by_uid(u2.uid, u.uid)

    def test_frozen_user_by_uid(self, user_svc, user_repo):
        """测试意图：管理员冻结用户后，用户状态应变为 FROZEN。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        admin_data = UserCreate(username="admin", phone="999", password="admin_pw")
        admin = user_svc.create_user(username=admin_data.username, phone=admin_data.phone, password=admin_data.password)
        user_repo.update_user(admin.uid, UserAdminPatch(role=UserRole.ADMIN))

        res = user_svc.frozen_user_by_uid(admin.uid, u.uid)
        assert res is not None
        assert res.user_info.status == UserStatus.FROZEN

    def test_user_to_admin(self, user_svc, user_repo):
        """测试意图：管理员提升用户为 ADMIN 时，目标用户角色应变更为 ADMIN。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        admin_data = UserCreate(username="admin", phone="999", password="admin_pw")
        admin = user_svc.create_user(username=admin_data.username, phone=admin_data.phone, password=admin_data.password)
        user_repo.update_user(admin.uid, UserAdminPatch(role=UserRole.ADMIN))

        res = user_svc.user_to_admin(admin.uid, u.uid)
        assert res is not None
        assert res.user_info.role == UserRole.ADMIN

    def test_user_to_moderator(self, user_svc, user_repo):
        """测试意图：管理员提升用户为 MODERATOR 时，目标用户角色应变更为 MODERATOR。"""
        user_data = UserCreate(username="u", phone="111", password="pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        admin_data = UserCreate(username="admin", phone="999", password="admin_pw")
        admin = user_svc.create_user(username=admin_data.username, phone=admin_data.phone, password=admin_data.password)
        user_repo.update_user(admin.uid, UserAdminPatch(role=UserRole.ADMIN))

        res = user_svc.user_to_moderator(admin.uid, u.uid)
        assert res is not None
        assert res.user_info.role == UserRole.MODERATOR

    def test_get_password(self, user_svc, user_repo):
        """测试意图：仓库应能获取到用户的密码 hash（用于登录/鉴权校验）。"""
        user_data = UserCreate(username="u", phone="111", password="old_pw")
        u = user_svc.create_user(username=user_data.username, phone=user_data.phone, password=user_data.password)

        password = user_repo.get_password(u.uid)
        assert password is not None

    def test_update_user_not_found(self, user_svc, user_repo):
        """测试意图：更新不存在用户时，service 应返回 None（而不是抛异常）。"""
        update_body = UserUpdate(user_info=UserInfoUpdateDto(username="new_u", bio="new bio"))

        result = user_svc.update_user("invalid_uid", update_body)
        assert result is None
