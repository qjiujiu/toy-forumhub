import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2 import users as users_api
from app.service.v2.user_svc import UserService
from app.schemas.v2.user import UserCreate, UserUpdate, UserInfoUpdateDto

from app.storage.v2.mock.mock_user import MockUserRepository


@pytest.fixture
def app():
    # API 单测这里也演示“数据库已有数据”的情况
    user_repo = MockUserRepository()

    api = FastAPI()
    api.include_router(users_api.users_router)

    def override_user_service() -> UserService:
        return UserService(user_repo)

    api.dependency_overrides[users_api.get_user_service] = override_user_service
    return api


@pytest.fixture
def client(app):
    return TestClient(app)


class TestUsersApiV2:
    def test_create_and_get_by_id_should_return_user(self, client: TestClient):
        """测试意图：创建用户后，通过 `/users/id/{uid}` 能查到该用户（BizResponse 包装结构正确）。"""
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
        """测试意图：查询不存在的用户，应返回 404 且 data 为 None。"""
        r = client.get("/users/id/not-exist")
        assert r.status_code == 404
        body = r.json()
        assert body["code"] == 404
        assert body["data"] is None

    def test_update_info_should_update_fields(self, client: TestClient):
        """测试意图：更新用户信息接口应只更新请求体字段，并返回更新后的用户信息。"""
        created = client.post("/users/", json={"username": "u1", "phone": "111", "password": "pw"}).json()
        uid = created["data"]["uid"]

        update_body = UserUpdate(user_info=UserInfoUpdateDto(username="u2", bio="bio")).model_dump()
        r = client.put(f"/users/info/id/{uid}", json=update_body)
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["user_info"]["username"] == "u2"
        assert body["data"]["user_info"]["bio"] == "bio"
