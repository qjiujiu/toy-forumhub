import pytest

from tests.mock.mock_like import MockLikeRepository
from tests.mock.mock_post import MockPostRepository
from tests.mock.mock_user import MockUserRepository
from tests.mock.mock_comment import MockCommentRepository

from app.schemas.v2.like import LikeCreate, LikeCancel, GetUserLike, GetTargetLike
from app.schemas.v2.post import PostCreate, PostDto
from app.schemas.v2.comment import CommentCreate
from app.schemas.v2.user import UserCreate
from app.service.v2.like_svc import LikeService

from app.kit.exceptions import AlreadyLikedError, NotLikedError


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
def like_repo():
    return MockLikeRepository.empty()


@pytest.fixture
def like_svc(like_repo, post_repo, comment_repo):
    return LikeService(like_repo, post_repo, comment_repo)


class TestLikeService:
    """测试 LikeService 业务逻辑层。"""

    # ==================== like() ====================

    def test_like_post(self, like_svc, post_repo, user_repo):
        """意图：为帖子点赞成功，like_count +1。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        result = like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        assert result.target_id == post.pid
        assert result.user_id == "u1"
        # 验证帖子 like_count 增加
        updated = post_repo.get_by_pid(post.pid)
        assert updated.post_stats.like_count == 1

    def test_like_comment(self, like_svc, post_repo, comment_repo, user_repo):
        """意图：为评论点赞成功，like_count +1。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        comment = comment_repo.create_comment(CommentCreate(post_id=post.pid, author_id=author.uid, content="nice"))
        result = like_svc.like(LikeCreate(user_id="u1", target_type=1, target_id=comment.cid))
        assert result.target_id == comment.cid
        # 验证评论 like_count 增加
        updated = comment_repo.get_by_cid(comment.cid)
        assert updated.like_count == 1

    def test_like_nonexistent_post_raises(self, like_svc, post_repo, user_repo):
        """意图：点赞不存在的帖子 → ValueError。"""
        with pytest.raises(ValueError, match="not found"):
            like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id="invalid_pid"))

    def test_like_nonexistent_comment_raises(self, like_svc, post_repo, user_repo):
        """意图：点赞不存在的评论 → ValueError。"""
        with pytest.raises(ValueError, match="not found"):
            like_svc.like(LikeCreate(user_id="u1", target_type=1, target_id="invalid_cid"))

    def test_like_twice_raises(self, like_svc, post_repo, user_repo):
        """意图：重复点赞同一目标 → AlreadyLikedError。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        with pytest.raises(AlreadyLikedError):
            like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))

    def test_like_then_cancel_then_like_again(self, like_svc, post_repo, user_repo):
        """意图：点赞→取消→再点赞，计数最终为 1。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        like_svc.cancel_like(LikeCancel(user_id="u1", target_type=0, target_id=post.pid))
        like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        updated = post_repo.get_by_pid(post.pid)
        assert updated.post_stats.like_count == 1

    # ==================== cancel_like() ====================

    def test_cancel_like_post(self, like_svc, post_repo, user_repo):
        """意图：取消帖子点赞，like_count -1 并不下溢。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        result = like_svc.cancel_like(LikeCancel(user_id="u1", target_type=0, target_id=post.pid))
        assert result is True
        updated = post_repo.get_by_pid(post.pid)
        assert updated.post_stats.like_count == 0

    def test_cancel_like_comment(self, like_svc, post_repo, comment_repo, user_repo):
        """意图：取消评论点赞，like_count -1。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        comment = comment_repo.create_comment(CommentCreate(post_id=post.pid, author_id=author.uid, content="c"))
        like_svc.like(LikeCreate(user_id="u1", target_type=1, target_id=comment.cid))
        like_svc.cancel_like(LikeCancel(user_id="u1", target_type=1, target_id=comment.cid))
        updated = comment_repo.get_by_cid(comment.cid)
        assert updated.like_count == 0

    def test_cancel_like_nonexistent_raises(self, like_svc, post_repo, user_repo):
        """意图：取消不存在的点赞 → NotLikedError。"""
        with pytest.raises(NotLikedError):
            like_svc.cancel_like(LikeCancel(user_id="u1", target_type=0, target_id="p1"))

    def test_cancel_twice_raises(self, like_svc, post_repo, user_repo):
        """意图：重复取消点赞 → NotLikedError。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        like_svc.cancel_like(LikeCancel(user_id="u1", target_type=0, target_id=post.pid))
        with pytest.raises(NotLikedError):
            like_svc.cancel_like(LikeCancel(user_id="u1", target_type=0, target_id=post.pid))

    # ==================== get_user_likes() ====================

    def test_get_user_likes(self, like_svc, post_repo, user_repo):
        """意图：获取用户点赞列表成功。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        result = like_svc.get_user_likes(GetUserLike(user_id="u1", target_type=0), to_dict=False)
        assert result.total == 1
        assert result.items[0].target_id == post.pid

    def test_get_user_likes_empty(self, like_svc, post_repo, user_repo):
        """意图：用户无点赞返回空列表。"""
        result = like_svc.get_user_likes(GetUserLike(user_id="u1", target_type=0), to_dict=False)
        assert result.total == 0

    # ==================== get_target_likes() ====================

    def test_get_target_likes(self, like_svc, post_repo, user_repo):
        """意图：获取目标点赞用户列表成功。"""
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        post = post_repo.create_post(PostCreate(author_id=author.uid, title="t", content="c", post_status=PostDto()))
        like_svc.like(LikeCreate(user_id="u1", target_type=0, target_id=post.pid))
        result = like_svc.get_target_likes(GetTargetLike(target_type=0, target_id=post.pid), to_dict=False)
        assert result.total == 1
        assert result.items[0].user_id == "u1"

    def test_get_target_likes_empty(self, like_svc, post_repo, user_repo):
        """意图：目标无点赞返回空列表。"""
        result = like_svc.get_target_likes(GetTargetLike(target_type=0, target_id="p1"), to_dict=False)
        assert result.total == 0
