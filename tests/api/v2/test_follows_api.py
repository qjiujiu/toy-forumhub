import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2 import follows as follows_api
from app.service.v2.follow_svc import FollowService

from tests.mock.mock_follow import MockFollowRepository
from tests.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate, UserInfoDto, UserUpdateDto
from app.models.v2.user import UserRole


@pytest.fixture
def app():
    """初始化 FastAPI 应用，使用 Mock 仓储 + dependency_overrides。"""
    user_repo = MockUserRepository()
    follow_repo = MockFollowRepository(user_repo=user_repo)

    # 预置两个用户
    u1 = user_repo.create_user(UserCreate(username="alice", phone="1111111111", password="pw"))
    u2 = user_repo.create_user(UserCreate(username="bob", phone="2222222222", password="pw"))
    admin = user_repo.create_user(UserCreate(username="admin", phone="9999999999", password="pw"))
    user_repo.update_user(admin.uid, UserUpdateDto(user_info=UserInfoDto(role=UserRole.ADMIN)))

    api = FastAPI()
    api.state.user_repo = user_repo
    api.state.follow_repo = follow_repo
    api.state.u1 = u1
    api.state.u2 = u2
    api.state.admin = admin
    api.include_router(follows_api.follows_router)

    def override_follow_service() -> FollowService:
        return FollowService(follow_repo, user_repo)

    api.dependency_overrides[follows_api.get_follow_service] = override_follow_service
    return api


@pytest.fixture
def client(app):
    return TestClient(app)


class TestFollowsApiV2:
    """测试 Follows API 路由层（基于 Mock 仓储 + TestClient）。"""

    # ==================== POST /follows/ ====================

    def test_follow_success(self, client: TestClient):
        """意图：关注成功返回 True。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        r = client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"] is True

    def test_follow_self_returns_400(self, client: TestClient):
        """意图：关注自己返回 400。"""
        u1 = client.app.state.u1
        r = client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u1.uid})
        assert r.status_code == 400

    def test_follow_duplicate_returns_400(self, client: TestClient):
        """意图：重复关注返回 400。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        r = client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        assert r.status_code == 400

    def test_follow_nonexistent_returns_404(self, client: TestClient):
        """意图：关注不存在的用户返回 404。"""
        u1 = client.app.state.u1
        r = client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": "invalid"})
        assert r.status_code == 404

    # ==================== DELETE /follows/ ====================

    def test_unfollow_success(self, client: TestClient):
        """意图：取消关注成功。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        r = client.request("DELETE", "/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        assert r.status_code == 200
        body = r.json()
        assert body["data"] is True

    def test_unfollow_nonexistent_returns_400(self, client: TestClient):
        """意图：取消不存在的关注返回 400。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        r = client.request("DELETE", "/follows/", json={"user_id": u1.uid,
                                                        "followed_user_id": u2.uid})
        assert r.status_code == 400

    # ==================== DELETE /follows/hard ====================

    def test_hard_unfollow_success(self, client: TestClient):
        """意图：管理员硬删除成功。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        admin = client.app.state.admin
        client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        r = client.request("DELETE", "/follows/hard",
                           params={"admin_uid": admin.uid},
                           json={"user_id": u1.uid, "followed_user_id": u2.uid})
        assert r.status_code == 200
        body = r.json()
        assert body["data"] is True

    def test_hard_unfollow_non_admin_returns_403(self, client: TestClient):
        """意图：非管理员硬删除返回 403。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        r = client.request("DELETE", "/follows/hard",
                           params={"admin_uid": u1.uid},
                           json={"user_id": u1.uid, "followed_user_id": u2.uid})
        assert r.status_code == 403

    # ==================== GET /follows/followings/{user_id} ====================

    def test_get_followings(self, client: TestClient):
        """意图：获取关注列表。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        r = client.get(f"/follows/followings/{u1.uid}")
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total"] == 1

    def test_get_followings_empty(self, client: TestClient):
        """意图：空关注列表。"""
        u1 = client.app.state.u1
        r = client.get(f"/follows/followings/{u1.uid}")
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["total"] == 0

    # ==================== GET /follows/followers/{user_id} ====================

    def test_get_followers(self, client: TestClient):
        """意图：获取粉丝列表。"""
        u1 = client.app.state.u1
        u2 = client.app.state.u2
        client.post("/follows/", json={"user_id": u1.uid, "followed_user_id": u2.uid})
        r = client.get(f"/follows/followers/{u2.uid}")
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total"] == 1

    def test_get_followers_empty(self, client: TestClient):
        """意图：空粉丝列表。"""
        u2 = client.app.state.u2
        r = client.get(f"/follows/followers/{u2.uid}")
        assert r.status_code == 200
        body = r.json()
        assert body["data"]["total"] == 0
