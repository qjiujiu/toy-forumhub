import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2 import users as users_api
from app.service.v2.user_svc import UserService

from tests.mock.mock_user import MockUserRepository


@pytest.fixture
def app():
    """初始化 FastAPI 应用，使用 Mock 存储 + dependency_overrides 替换真实依赖。"""
    user_repo = MockUserRepository()

    api = FastAPI()
    api.include_router(users_api.users_router)
    api.state.user_repo = user_repo

    def override_user_service() -> UserService:
        return UserService(user_repo)

    api.dependency_overrides[users_api.get_user_service] = override_user_service
    return api


@pytest.fixture
def client(app):
    return TestClient(app)


class TestUsersApiV2:
    """测试 Users API 路由层（基于 Mock 仓储 + TestClient）。"""

    def test_create_and_get_by_id(self, client: TestClient):
        """意图：创建用户后，通过 /users/id/{uid} 能查到该用户（BizResponse 包装结构正确）。"""
        payload = {"username": "u1", "phone": "111", "password": "pw"}
        r = client.post("/users/", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["msg"] == "success"
        assert body["data"]["user_info"]["username"] == "u1"
        uid = body["data"]["uid"]

        r2 = client.get(f"/users/id/{uid}")
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2["code"] == 200
        assert body2["data"]["uid"] == uid

    def test_get_by_id_should_return_404_when_not_found(self, client: TestClient):
        """意图：查询不存在的用户，应返回 404 且 data 为 None。"""
        r = client.get("/users/id/not-exist")
        assert r.status_code == 404
        body = r.json()
        assert body["code"] == 404
        assert body["data"] is None

    def test_create_and_get_by_username(self, client: TestClient):
        """意图：按用户名查询用户列表。"""
        client.post("/users/", json={"username": "same", "phone": "111", "password": "pw"})
        client.post("/users/", json={"username": "same", "phone": "222", "password": "pw"})
        r = client.get("/users/username/same")
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total"] == 2

    def test_get_batch_users(self, client: TestClient):
        """意图：分页获取用户列表。"""
        client.post("/users/", json={"username": "a", "phone": "111", "password": "pw"})
        client.post("/users/", json={"username": "b", "phone": "222", "password": "pw"})
        r = client.get("/users/", params={"page": 0, "page_size": 10})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total"] >= 2

    def test_get_profile(self, client: TestClient):
        """意图：获取用户 profile（含统计信息）。"""
        created = client.post("/users/", json={"username": "u1", "phone": "111", "password": "pw"}).json()
        uid = created["data"]["uid"]
        r = client.get(f"/users/profile/{uid}")
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["user_info"]["uid"] == uid
        assert body["data"]["user_stats"]["following_count"] == 0
        assert body["data"]["user_stats"]["followers_count"] == 0

    def test_update_info(self, client: TestClient):
        """意图：更新用户信息接口应只更新请求体字段，并返回更新后的用户信息。"""
        created = client.post("/users/", json={"username": "u1", "phone": "111", "password": "pw"}).json()
        uid = created["data"]["uid"]
        update_body = {"username": "u2", "bio": "bio"}
        r = client.put(f"/users/info/id/{uid}", json=update_body)
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["user_info"]["username"] == "u2"
        assert body["data"]["user_info"]["bio"] == "bio"

    def test_soft_delete_user(self, client: TestClient):
        """意图：软删除用户后，通过 id 查询返回 404。"""
        created = client.post("/users/", json={"username": "u1", "phone": "111", "password": "pw"}).json()
        uid = created["data"]["uid"]
        r = client.delete(f"/users/soft/id/{uid}")
        assert r.status_code == 200
        r2 = client.get(f"/users/id/{uid}")
        assert r2.status_code == 404

    def test_profile_not_found(self, client: TestClient):
        """意图：不存在的用户 profile 返回 404。"""
        r = client.get("/users/profile/nonexistent")
        assert r.status_code == 404
