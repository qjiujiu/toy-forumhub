import pytest

from tests.mock.mock_post import (
    MockPostRepository,
    MockPostContentRepository,
    MockPostStatsRepository,
)
from tests.mock.mock_user import MockUserRepository, MockUserStatsRepository

from app.schemas.v2.post import PostCreate, PostUpdate, PostDto
from app.schemas.v2.post_content import PostContentUpdate
from app.schemas.v2.user import UserCreate, UserInfoDto, UserUpdateDto, UserRole, UserStatus
from app.service.v2.post_svc import PostService

from app.core.exceptions import PostNotFound, ForbiddenAction, AdminPermissionDenied


@pytest.fixture
def post_repo():
    return MockPostRepository()


@pytest.fixture
def content_repo():
    return MockPostContentRepository(None)


@pytest.fixture
def stats_repo():
    return MockPostStatsRepository(None)


@pytest.fixture
def setup_repos(post_repo, content_repo, stats_repo):
    post_repo.set_related_repos(content_repo, stats_repo)
    content_repo.post_repo = post_repo
    stats_repo.post_repo = post_repo


@pytest.fixture
def user_repo():
    return MockUserRepository()


@pytest.fixture
def user_stats_repo(user_repo):
    return MockUserStatsRepository(user_repo)


@pytest.fixture
def post_svc(post_repo, content_repo, stats_repo, user_repo, user_stats_repo, setup_repos):
    return PostService(post_repo, content_repo, stats_repo, user_repo)


class TestPostService:
    def test_create_post(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostDto(),
        )

        result = post_svc.create_post(post_data, to_dict=False)

        assert result.author_id == author.uid
        assert result.post_content is not None
        assert result.post_content.title == "Test Post"
        assert result.post_stats.like_count == 0
        assert result.post_stats.comment_count == 0

    def test_get_post(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostDto(),
        )

        created = post_svc.create_post(post_data, to_dict=False)

        result = post_svc.get_post(created.pid, to_dict=False)
        assert result is not None
        assert result.pid == created.pid

        with pytest.raises(PostNotFound):
            post_svc.get_post("invalid_pid", to_dict=False)

    def test_get_posts_by_author(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        for i in range(3):
            post_data = PostCreate(
                author_id=author.uid,
                title=f"Post {i}",
                content=f"Content {i}",
                post_status=PostDto(),
            )
            post_svc.create_post(post_data, to_dict=False)

        result = post_svc.get_posts_by_author(author.uid, page=0, page_size=10, to_dict=False)
        assert result.total == 3
        assert result.count == 3

    def test_update_post_content(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        post_data = PostCreate(
            author_id=author.uid,
            title="Original Title",
            content="Original content",
            post_status=PostDto(),
        )

        created = post_svc.create_post(post_data, to_dict=False)

        update_data = PostContentUpdate(
            title="Updated Title",
            content="Updated content",
        )

        result = post_svc.update_post_content(author.uid, created.pid, update_data, to_dict=False)
        assert result.post_content.title == "Updated Title"
        assert result.post_content.content == "Updated content"

        with pytest.raises(ForbiddenAction):
            post_svc.update_post_content("other_user", created.pid, update_data)

    def test_update_post_visibility(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostDto(),
        )

        created = post_svc.create_post(post_data, to_dict=False)

        update_data = PostUpdate(visibility=1)

        result = post_svc.update_post_visibility(author.uid, created.pid, update_data, to_dict=False)
        assert result.post_status.visibility == 1

    def test_ban_post(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        admin_data = UserCreate(username="admin", phone="9999999999", password="admin_pw")
        admin = user_repo.create_user(admin_data)
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostDto(),
        )

        created = post_svc.create_post(post_data, to_dict=False)

        result = post_svc.ban_post(admin.uid, created.pid, to_dict=False)
        assert result.post_status.publish_status == 2

        with pytest.raises(AdminPermissionDenied):
            post_svc.ban_post(author.uid, created.pid)

    def test_publish_post(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        post_data = PostCreate(
            author_id=author.uid,
            title="Draft Post",
            content="Draft content",
            post_status=PostDto(publish_status=0),
        )

        created = post_svc.create_post(post_data, to_dict=False)

        result = post_svc.publish_post(author.uid, created.pid, to_dict=False)
        assert result.post_status.publish_status == 1

        with pytest.raises(ForbiddenAction):
            post_svc.publish_post("other_user", created.pid)

    def test_soft_delete_post(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        user_data2 = UserCreate(username="author2", phone="2234567890", password="password")
        author2 = user_repo.create_user(user_data2)

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostDto(),
        )

        created = post_svc.create_post(post_data, to_dict=False)

        with pytest.raises(ForbiddenAction):
            post_svc.soft_delete_post(author2.uid, created.pid)

        result = post_svc.soft_delete_post(author.uid, created.pid)
        assert result is True

        with pytest.raises(PostNotFound):
            post_svc.get_post(created.pid, to_dict=False)

    def test_hard_delete_post(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        admin_data = UserCreate(username="admin", phone="9999999999", password="admin_pw")
        admin = user_repo.create_user(admin_data)
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))

        post_data = PostCreate(
            author_id=author.uid,
            title="Test Post",
            content="Test content",
            post_status=PostDto(),
        )

        created = post_svc.create_post(post_data, to_dict=False)

        result = post_svc.hard_delete_post(admin.uid, created.pid)
        assert result is True

        post = post_repo.get_by_pid(created.pid)
        assert post is None

        with pytest.raises(AdminPermissionDenied):
            post_svc.hard_delete_post(author.uid, created.pid)

    def test_get_top_liked_posts(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author", phone="1234567890", password="password")
        author = user_repo.create_user(user_data)

        for i in range(5):
            post_data = PostCreate(
                author_id=author.uid,
                title=f"Liked Post {i}",
                content=f"Content {i}",
                post_status=PostDto(),
            )
            post_svc.create_post(post_data, to_dict=False)

        result = post_svc.get_top_liked_posts(limit=10, to_dict=False)
        assert len(result) <= 10

    def test_get_top_commented_posts(self, post_svc, post_repo, content_repo, stats_repo, user_repo):
        from app.schemas.v2.user import UserCreate

        user_data = UserCreate(username="author2", phone="2234567890", password="password")
        author = user_repo.create_user(user_data)

        for i in range(5):
            post_data = PostCreate(
                author_id=author.uid,
                title=f"Commented Post {i}",
                content=f"Content {i}",
                post_status=PostDto(),
            )
            post_svc.create_post(post_data, to_dict=False)

        result = post_svc.get_top_commented_posts(limit=10, to_dict=False)
        assert len(result) <= 10