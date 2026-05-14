# python -m pytest tests/service/test_post_svc.py -v
import pytest

from tests.mock.mock_post import MockPostRepository
from tests.mock.mock_user import MockUserRepository

from app.schemas.v2.post import PostCreate, PostUpdate, PostDto
from app.schemas.v2.post_content import PostContentUpdate
from app.schemas.v2.user import UserCreate, UserInfoDto, UserUpdateDto
from app.models.v2.user import UserRole
from app.service.v2.post_svc import PostService

from app.kit.exceptions import PostNotFound, ForbiddenAction, AdminPermissionDenied


@pytest.fixture
def user_repo():
    return MockUserRepository.empty()


@pytest.fixture
def post_repo(user_repo):
    return MockPostRepository.empty(user_repo=user_repo)


@pytest.fixture
def post_svc(post_repo, user_repo):
    return PostService(post_repo, user_repo)


class TestPostService:
    """测试 PostService 业务逻辑层（基于聚合仓储 + Mock）。"""

    def test_create_post(self, post_svc, post_repo, user_repo):
        """意图：创建帖子时，应一次性生成帖子聚合（基础信息 + content + stats），且统计默认值正确。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        post_data = PostCreate(author_id=author.uid, title="Test Post", content="Test content", post_status=PostDto())
        result = post_svc.create_post(post_data, to_dict=False)
        assert result.author_id == author.uid
        assert result.post_content is not None
        assert result.post_content.title == "Test Post"
        assert result.post_stats.like_count == 0
        assert result.post_stats.comment_count == 0

    def test_get_post(self, post_svc, post_repo, user_repo):
        """意图：按 pid 获取帖子应返回正确对象；pid 不存在应抛 PostNotFound。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Test Post", content="Test content", post_status=PostDto()),
            to_dict=False,
        )
        result = post_svc.get_post(created.pid, to_dict=False)
        assert result is not None
        assert result.pid == created.pid
        with pytest.raises(PostNotFound):
            post_svc.get_post("invalid_pid")

    def test_get_posts_by_author(self, post_svc, post_repo, user_repo):
        """意图：按作者查询帖子列表，应只返回该作者帖子，分页计数正确。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        for i in range(3):
            post_svc.create_post(
                PostCreate(author_id=author.uid, title=f"Post {i}", content=f"Content {i}", post_status=PostDto()),
                to_dict=False,
            )
        result = post_svc.get_posts_by_author(author.uid, page=0, page_size=10, to_dict=False)
        assert result.total == 3
        assert result.count == 3

    def test_update_post_content(self, post_svc, post_repo, user_repo):
        """意图：作者更新帖子内容应成功；非作者更新应抛 ForbiddenAction。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Original Title", content="Original content", post_status=PostDto()),
            to_dict=False,
        )
        update_data = PostContentUpdate(title="Updated Title", content="Updated content")
        result = post_svc.update_post_content(author.uid, created.pid, update_data, to_dict=False)
        assert result.post_content.title == "Updated Title"
        assert result.post_content.content == "Updated content"
        with pytest.raises(ForbiddenAction):
            post_svc.update_post_content("other_user", created.pid, update_data)

    def test_update_post_visibility(self, post_svc, post_repo, user_repo):
        """意图：作者更新帖子可见性，只应影响 visibility 字段。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Test Post", content="Test content", post_status=PostDto()),
            to_dict=False,
        )
        result = post_svc.update_post_visibility(author.uid, created.pid, PostUpdate(visibility=1), to_dict=False)
        assert result.post_status.visibility == 1

    def test_ban_post(self, post_svc, post_repo, user_repo):
        """意图：管理员封禁帖子应将 publish_status 置为 2；非管理员应抛 AdminPermissionDenied。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        admin = user_repo.create_user(UserCreate(username="admin", phone="9999999999", password="admin_pw"))
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Test Post", content="Test content", post_status=PostDto()),
            to_dict=False,
        )
        result = post_svc.ban_post(admin.uid, created.pid, to_dict=False)
        assert result.post_status.publish_status == 2
        with pytest.raises(AdminPermissionDenied):
            post_svc.ban_post(author.uid, created.pid)

    def test_publish_post(self, post_svc, post_repo, user_repo):
        """意图：作者发布草稿帖子应成功（publish_status 0→1）；非作者应抛 ForbiddenAction。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Draft Post", content="Draft content", post_status=PostDto(publish_status=0)),
            to_dict=False,
        )
        result = post_svc.publish_post(author.uid, created.pid, to_dict=False)
        assert result.post_status.publish_status == 1
        with pytest.raises(ForbiddenAction):
            post_svc.publish_post("other_user", created.pid)

    def test_publish_already_published_raises(self, post_svc, post_repo, user_repo):
        """意图：对已发布的帖子再次 publish 应抛 ForbiddenAction。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Published", content="c", post_status=PostDto(publish_status=1)),
            to_dict=False,
        )
        with pytest.raises(ForbiddenAction, match="only draft"):
            post_svc.publish_post(author.uid, created.pid)

    def test_soft_delete_post(self, post_svc, post_repo, user_repo):
        """意图：软删除需要作者权限；软删后 get_post 应抛 PostNotFound。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        author2 = user_repo.create_user(UserCreate(username="author2", phone="2234567890", password="password"))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Test Post", content="Test content", post_status=PostDto()),
            to_dict=False,
        )
        with pytest.raises(ForbiddenAction):
            post_svc.soft_delete_post(author2.uid, created.pid)
        result = post_svc.soft_delete_post(author.uid, created.pid)
        assert result is True
        with pytest.raises(PostNotFound):
            post_svc.get_post(created.pid)

    def test_hard_delete_post(self, post_svc, post_repo, user_repo):
        """意图：硬删除需要管理员权限；成功后帖子应从仓库中移除。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        admin = user_repo.create_user(UserCreate(username="admin", phone="9999999999", password="admin_pw"))
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        created = post_svc.create_post(
            PostCreate(author_id=author.uid, title="Test Post", content="Test content", post_status=PostDto()),
            to_dict=False,
        )
        result = post_svc.hard_delete_post(admin.uid, created.pid)
        assert result is True
        assert post_repo.get_by_pid(created.pid) is None
        with pytest.raises(AdminPermissionDenied):
            post_svc.hard_delete_post(author.uid, created.pid)

    def test_get_top_liked_posts(self, post_svc, post_repo, user_repo):
        """意图：获取点赞榜接口应返回不超过 limit 的帖子集合。"""
        author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="password"))
        for i in range(5):
            post_svc.create_post(
                PostCreate(author_id=author.uid, title=f"Liked Post {i}", content=f"Content {i}", post_status=PostDto()),
                to_dict=False,
            )
        result = post_svc.get_top_liked_posts(limit=10, to_dict=False)
        assert len(result) <= 10

    def test_get_top_commented_posts(self, post_svc, post_repo, user_repo):
        """意图：获取评论榜接口应返回不超过 limit 的帖子集合。"""
        author = user_repo.create_user(UserCreate(username="author2", phone="2234567890", password="password"))
        for i in range(5):
            post_svc.create_post(
                PostCreate(author_id=author.uid, title=f"Commented Post {i}", content=f"Content {i}", post_status=PostDto()),
                to_dict=False,
            )
        result = post_svc.get_top_commented_posts(limit=10, to_dict=False)
        assert len(result) <= 10
