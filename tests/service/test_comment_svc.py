import pytest

from tests.mock.mock_comment import MockCommentRepository
from tests.mock.mock_post import MockPostRepository
from tests.mock.mock_user import MockUserRepository

from app.schemas.v2.comment import CommentCreate, CommentQueryDTO, StatusUpdate
from app.schemas.v2.post import PostDto, PostCreate
from app.schemas.v2.user import UserCreate, UserInfoDto, UserUpdateDto
from app.models.v2.user import UserRole
from app.service.v2.comment_svc import CommentService

from app.core.exceptions import CommentNotFound, AdminPermissionDenied, UserNotFound


@pytest.fixture
def user_repo():
    return MockUserRepository.empty()


@pytest.fixture
def post_repo(user_repo):
    return MockPostRepository.empty(user_repo=user_repo)


@pytest.fixture
def comment_repo(post_repo, user_repo):
    return MockCommentRepository.empty(post_repo=post_repo, user_repo=user_repo)


@pytest.fixture
def comment_svc(comment_repo, post_repo, user_repo):
    return CommentService(comment_repo, post_repo, user_repo)


class TestCommentService:
    """测试 CommentService 业务逻辑层（基于聚合仓储 + Mock）。"""

    def test_create_comment(self, comment_svc, post_repo, user_repo):
        """意图：创建评论成功，返回完整评论数据。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        result = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="nice post!"),
            to_dict=True,
        )
        assert result["cid"] is not None
        assert result["comment_content"]["content"] == "nice post!"

    def test_create_comment_without_post_raises(self, comment_svc, post_repo, user_repo):
        """意图：帖子不存在时创建评论应抛 ValueError。"""
        with pytest.raises(ValueError, match="not found"):
            comment_svc.create_comment(CommentCreate(post_id="invalid", author_id="a1", content="c"))

    def test_get_comment(self, comment_svc, post_repo, user_repo):
        """意图：获取存在的评论返回正确对象；不存在的返回 None。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        created_dict = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="hello"),
            to_dict=True,
        )
        cid = created_dict["cid"]
        found = comment_svc.get_comment(cid)
        assert found is not None
        assert found.cid == cid
        assert comment_svc.get_comment("nonexistent") is None

    def test_get_comments(self, comment_svc, post_repo, user_repo):
        """意图：查询评论列表正确返回总数和分页。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        for i in range(3):
            comment_svc.create_comment(
                CommentCreate(post_id=post.pid, author_id=author.uid, content=f"c{i}"),
                to_dict=False,
            )
        result = comment_svc.get_comments_by_post_id(post_id=post.pid, page=0, page_size=10)
        assert result.total == 3
        assert result.count == 3

    def test_update_comment_as_admin(self, comment_svc, post_repo, user_repo):
        """意图：管理员更新评论状态成功。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        admin = user_repo.create_user(UserCreate(username="admin", phone="999", password="pw"))
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        c_dict = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="c"),
            to_dict=True,
        )
        cid = c_dict["cid"]
        result = comment_svc.update_comment(admin.uid, cid, StatusUpdate(status=1))
        assert result is True
        found = comment_svc.get_comment(cid)
        assert found.status == 1

    def test_update_comment_non_admin_raises(self, comment_svc, post_repo, user_repo):
        """意图：非管理员更新评论状态应抛 AdminPermissionDenied。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        c_dict = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="c"),
            to_dict=True,
        )
        with pytest.raises(AdminPermissionDenied):
            comment_svc.update_comment(author.uid, c_dict["cid"], StatusUpdate(status=1))

    def test_delete_comment(self, comment_svc, post_repo, user_repo):
        """意图：软删除评论后，get_comment 返回 None。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        c_dict = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="c"),
            to_dict=True,
        )
        cid = c_dict["cid"]
        result = comment_svc.delete_comment(cid)
        assert result is True
        assert comment_svc.get_comment(cid) is None

    def test_hard_delete_comment_as_admin(self, comment_svc, post_repo, user_repo):
        """意图：管理员硬删除评论成功。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        admin = user_repo.create_user(UserCreate(username="admin", phone="999", password="pw"))
        user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        c_dict = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="c"),
            to_dict=True,
        )
        cid = c_dict["cid"]
        result = comment_svc.hard_delete_comment(admin.uid, cid)
        assert result is True
        assert comment_svc.get_comment(cid) is None

    def test_hard_delete_comment_non_admin_raises(self, comment_svc, post_repo, user_repo):
        """意图：非管理员硬删除评论应抛 AdminPermissionDenied。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        c_dict = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="c"),
            to_dict=True,
        )
        with pytest.raises(AdminPermissionDenied):
            comment_svc.hard_delete_comment(author.uid, c_dict["cid"])

    def test_get_post_by_comment_cid(self, comment_svc, post_repo, user_repo):
        """意图：通过评论 cid 获取关联帖子。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(
            PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto())
        )
        c_dict = comment_svc.create_comment(
            CommentCreate(post_id=post.pid, author_id=author.uid, content="c"),
            to_dict=True,
        )
        cid = c_dict["cid"]
        result = comment_svc.get_post_by_comment_cid(cid, to_dict=True)
        assert result["pid"] == post.pid
        with pytest.raises(CommentNotFound):
            comment_svc.get_post_by_comment_cid("invalid", to_dict=False)

    def test_delete_nonexistent_comment(self, comment_svc, post_repo, user_repo):
        """意图：删除不存在的评论返回 False。"""
        result = comment_svc.delete_comment("nonexistent")
        assert result is False
