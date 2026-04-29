import pytest

from app.storage.v2.mock.mock_post import (
    MockPostRepository,
)
from app.storage.v2.mock.mock_user import MockUserRepository

from app.schemas.v2.post import PostCreate, PostUpdate, PostStatus
from app.schemas.v2.post_content import PostContentUpdate
from app.schemas.v2.user import UserCreate
from app.models.v2.user import UserRole
from app.schemas.v2.user_req import UserAdminPatch
from app.service.v2.post_svc import PostService

from app.core.exceptions import PostNotFound, ForbiddenAction, AdminPermissionDenied


@pytest.fixture
def user_repo():
    # service 单测默认使用“干净仓库”，避免被预置数据干扰断言
    return MockUserRepository.empty()


@pytest.fixture
def post_repo(user_repo):
    # 知识点：SQLAlchemy repo 需要 join users 数据表拿作者信息 (多表联查), mock 通过注入 user_repo 来模拟。
    return MockPostRepository.empty(user_repo=user_repo)


@pytest.fixture
def post_svc(post_repo, user_repo):
    return PostService(post_repo, user_repo)


class TestPostService:
    def test_create_post(self, post_svc, post_repo, user_repo):
        """测试意图：创建帖子时，应一次性生成帖子聚合（基础信息 + content + stats），且统计默认值正确。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostStatus(),
        )

        result = post_svc.create_post(post_data)

        assert result.author_id == author.uid
        assert result.post_content is not None
        assert result.post_content.title == "Test Post"
        assert result.post_stats.like_count == 0
        assert result.post_stats.comment_count == 0

    def test_get_post(self, post_svc, post_repo, user_repo):
        """测试意图：按 pid 获取帖子应返回正确对象；pid 不存在应抛 PostNotFound。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostStatus(),
        )

        created = post_svc.create_post(post_data)

        result = post_svc.get_post(created.pid)
        assert result is not None
        assert result.pid == created.pid

        with pytest.raises(PostNotFound):
            post_svc.get_post("invalid_pid")

    def test_get_posts_by_author(self, post_svc, post_repo, user_repo):
        """测试意图：按作者查询帖子列表时，应只返回该作者帖子，并且分页计数正确。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        for i in range(3):
            post_data = PostCreate(
                author_id=author.uid,
                title=f"Post {i}",
                content=f"Content {i}",
                post_status=PostStatus(),
            )
            post_svc.create_post(post_data)

        result = post_svc.get_posts_by_author(author.uid, page=0, page_size=10)
        assert result.total == 3
        assert result.count == 3

    def test_update_post_content(self, post_svc, post_repo, user_repo):
        """测试意图：作者更新帖子内容应成功；非作者更新应抛 ForbiddenAction。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        post_data = PostCreate(
            author_id=author.uid,
            title="Original Title",
            content="Original content",
            post_status=PostStatus(),
        )

        created = post_svc.create_post(post_data)

        update_data = PostContentUpdate(
            title="Updated Title",
            content="Updated content",
        )

        result = post_svc.update_post_content(author.uid, created.pid, update_data)
        assert result.post_content.title == "Updated Title"
        assert result.post_content.content == "Updated content"

        with pytest.raises(ForbiddenAction):
            post_svc.update_post_content("other_user", created.pid, update_data)

    def test_update_post_visibility(self, post_svc, post_repo, user_repo):
        """测试意图：作者更新帖子可见性时，只应影响 visibility 字段并返回更新结果。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostStatus(),
        )

        created = post_svc.create_post(post_data)

        update_data = PostUpdate(visibility=1)

        result = post_svc.update_post_visibility(author.uid, created.pid, update_data)
        assert result.post_status.visibility == 1

    def test_ban_post(self, post_svc, post_repo, user_repo):
        """测试意图：管理员封禁帖子应将 publish_status 置为封禁态；非管理员封禁应抛 AdminPermissionDenied。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        admin_data = UserCreate(username="admin", phone="9999999999", password="admin_pw")
        admin = user_repo.create_user(username=admin_data.username, phone=admin_data.phone, hashed_password=admin_data.password)
        user_repo.update_user(admin.uid, UserAdminPatch(role=UserRole.ADMIN))

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostStatus(),
        )

        created = post_svc.create_post(post_data)

        result = post_svc.ban_post(admin.uid, created.pid)
        assert result.post_status.publish_status == 2

        with pytest.raises(AdminPermissionDenied):
            post_svc.ban_post(author.uid, created.pid)

    def test_publish_post(self, post_svc, post_repo, user_repo):
        """测试意图：作者发布帖子应成功（publish_status 变更）；非作者发布应抛 ForbiddenAction。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        post_data = PostCreate(
            author_id=author.uid,
            title="Draft Post",
            content="Draft content",
            post_status=PostStatus(publish_status=0),
        )

        created = post_svc.create_post(post_data)

        result = post_svc.publish_post(author.uid, created.pid)
        assert result.post_status.publish_status == 1

        with pytest.raises(ForbiddenAction):
            post_svc.publish_post("other_user", created.pid)

    def test_soft_delete_post(self, post_svc, post_repo, user_repo):
        """测试意图：软删除帖子需要作者权限；软删后帖子应在读路径不可见（get_post 抛 PostNotFound）。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        user_data2 = UserCreate(username="author2", phone="2234567890", password="password")
        author2 = user_repo.create_user(username=user_data2.username, phone=user_data2.phone, hashed_password=user_data2.password)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostStatus(),
        )

        created = post_svc.create_post(post_data)

        with pytest.raises(ForbiddenAction):
            post_svc.soft_delete_post(author2.uid, created.pid)

        result = post_svc.soft_delete_post(author.uid, created.pid)
        assert result is True

        with pytest.raises(PostNotFound):
            post_svc.get_post(created.pid)

    def test_hard_delete_post(self, post_svc, post_repo, user_repo):
        """测试意图：硬删除帖子需要管理员权限；成功后帖子应从仓库中完全移除。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        admin_data = UserCreate(username="admin", phone="9999999999", password="admin_pw")
        admin = user_repo.create_user(username=admin_data.username, phone=admin_data.phone, hashed_password=admin_data.password)
        user_repo.update_user(admin.uid, UserAdminPatch(role=UserRole.ADMIN))

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostStatus(),
        )

        created = post_svc.create_post(post_data)

        result = post_svc.hard_delete_post(admin.uid, created.pid)
        assert result is True

        post = post_repo.get_by_pid(created.pid)
        assert post is None

        with pytest.raises(AdminPermissionDenied):
            post_svc.hard_delete_post(author.uid, created.pid)

    def test_get_top_liked_posts(self, post_svc, post_repo, user_repo):
        """测试意图：获取点赞榜接口应返回不超过 limit 的帖子集合。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        for i in range(5):
            post_data = PostCreate(
                author_id=author.uid,
                title=f"Liked Post {i}",
                content=f"Content {i}",
                post_status=PostStatus(),
            )
            post_svc.create_post(post_data)

        result = post_svc.get_top_liked_posts(limit=10)
        assert len(result) <= 10

    def test_get_top_commented_posts(self, post_svc, post_repo, user_repo):
        """测试意图：获取评论榜接口应返回不超过 limit 的帖子集合。"""
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author2", phone="2234567890", password="password")
        author = user_repo.create_user(username=user_data.username, phone=user_data.phone, hashed_password=user_data.password)

        for i in range(5):
            post_data = PostCreate(
                author_id=author.uid,
                title=f"Commented Post {i}",
                content=f"Content {i}",
                post_status=PostStatus(),
            )
            post_svc.create_post(post_data)

        result = post_svc.get_top_commented_posts(limit=10)
        assert len(result) <= 10
