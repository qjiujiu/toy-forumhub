import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2 import likes as likes_api
from app.service.v2.like_svc import LikeService

from tests.mock.mock_like import MockLikeRepository
from tests.mock.mock_post import MockPostRepository
from tests.mock.mock_user import MockUserRepository
from tests.mock.mock_comment import MockCommentRepository

from app.schemas.v2.post import PostCreate, PostDto
from app.schemas.v2.comment import CommentCreate
from app.schemas.v2.user import UserCreate


@pytest.fixture
def app():
    """初始化 FastAPI 应用，使用 Mock 仓储 + dependency_overrides。"""
    user_repo = MockUserRepository()
    post_repo = MockPostRepository(user_repo=user_repo)
    comment_repo = MockCommentRepository(post_repo=post_repo, user_repo=user_repo)
    like_repo = MockLikeRepository()

    # 预置数据：一个作者用户 + 一篇文章 + 一条评论
    author = user_repo.create_user(UserCreate(username="author", phone="1234567890", password="pw"))
    post = post_repo.create_post(PostCreate(author_id=author.uid, title="Test Post", content="Content", post_status=PostDto()))
    comment = comment_repo.create_comment(CommentCreate(post_id=post.pid, author_id=author.uid, content="Nice!"))

    api = FastAPI()
    api.state.user_repo = user_repo
    api.state.post_repo = post_repo
    api.state.comment_repo = comment_repo
    api.state.like_repo = like_repo
    api.state.seeded_author = author
    api.state.seeded_post = post
    api.state.seeded_comment = comment

    api.include_router(likes_api.likes_router)

    def override_like_service() -> LikeService:
        return LikeService(like_repo, post_repo, comment_repo)

    api.dependency_overrides[likes_api.get_like_service] = override_like_service
    return api


@pytest.fixture
def client(app):
    return TestClient(app)


class TestLikesApiV2:
    """测试 Likes API 路由层（基于 Mock 仓储 + TestClient）。"""

    # ==================== POST /likes/ ====================

    def test_like_post(self, client: TestClient):
        """意图：为帖子点赞成功，返回 LikeOut。"""
        post = client.app.state.seeded_post
        r = client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["target_id"] == post.pid
        assert body["data"]["user_id"] == "u1"

    def test_like_comment(self, client: TestClient):
        """意图：为评论点赞成功。"""
        comment = client.app.state.seeded_comment
        r = client.post("/likes/", json={"user_id": "u1", "target_type": 1, "target_id": comment.cid})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["target_id"] == comment.cid

    def test_like_duplicate_returns_400(self, client: TestClient):
        """意图：重复点赞同一目标返回 400。"""
        post = client.app.state.seeded_post
        client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        r = client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        assert r.status_code == 400
        body = r.json()
        assert body["code"] == 400

    def test_like_nonexistent_target_returns_400(self, client: TestClient):
        """意图：点赞不存在的目标返回 400。"""
        r = client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": "invalid"})
        assert r.status_code == 400

    # ==================== DELETE /likes/ ====================

    def test_cancel_like(self, client: TestClient):
        """意图：取消点赞成功。"""
        post = client.app.state.seeded_post
        client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        r = client.request("DELETE", "/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"] is True

    def test_cancel_nonexistent_returns_400(self, client: TestClient):
        """意图：取消不存在的点赞返回 400。"""
        r = client.request("DELETE", "/likes/", json={"user_id": "u1", "target_type": 0, "target_id": "p1"})
        assert r.status_code == 400

    def test_cancel_twice_returns_400(self, client: TestClient):
        """意图：重复取消点赞返回 400。"""
        post = client.app.state.seeded_post
        client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        client.request("DELETE", "/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        r = client.request("DELETE", "/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        assert r.status_code == 400

    # ==================== GET /likes/user ====================

    def test_get_user_likes(self, client: TestClient):
        """意图：获取用户点赞列表成功。"""
        post = client.app.state.seeded_post
        client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        r = client.get("/likes/user", params={"user_id": "u1", "target_type": 0})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total"] >= 1
        assert body["data"]["items"][0]["target_id"] == post.pid

    def test_get_user_likes_empty(self, client: TestClient):
        """意图：用户无点赞返回空列表。"""
        r = client.get("/likes/user", params={"user_id": "noone", "target_type": 0})
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["total"] == 0

    # ==================== GET /likes/target ====================

    def test_get_target_likes(self, client: TestClient):
        """意图：获取目标点赞用户列表成功。"""
        post = client.app.state.seeded_post
        client.post("/likes/", json={"user_id": "u1", "target_type": 0, "target_id": post.pid})
        r = client.get("/likes/target", params={"target_type": 0, "target_id": post.pid})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total"] >= 1
        assert body["data"]["items"][0]["user_id"] == "u1"

    def test_get_target_likes_empty(self, client: TestClient):
        """意图：目标无点赞返回空列表。"""
        r = client.get("/likes/target", params={"target_type": 0, "target_id": "nopost"})
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["total"] == 0
