import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2 import posts as posts_api
from app.service.v2.post_svc import PostService

from tests.mock.mock_post import MockPostRepository
from tests.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate


@pytest.fixture
def app():
    """初始化 FastAPI 应用，使用 Mock 存储 + dependency_overrides 替换真实依赖。"""
    user_repo = MockUserRepository()
    post_repo = MockPostRepository(user_repo=user_repo)

    # 预置一个作者用户（API 测试需要数据库中有用户数据）
    user_repo.create_user(UserCreate(username="test_author", phone="1234567890", password="pw"))

    api = FastAPI()
    api.state.user_repo = user_repo
    api.state.post_repo = post_repo
    api.include_router(posts_api.posts_router)

    def override_post_service() -> PostService:
        return PostService(post_repo, user_repo)

    api.dependency_overrides[posts_api.get_post_service] = override_post_service
    return api


@pytest.fixture
def client(app):
    return TestClient(app)


class TestPostsApiV2:
    """测试 Posts API 路由层（基于 Mock 仓储 + TestClient）。"""

    def _author(self, client):
        return client.app.state.user_repo.list_users(page=0, page_size=1).users[0]

    def _create_post(self, client, author_uid, title="t", content="c", **extra):
        payload = {"author_id": author_uid, "title": title, "content": content, "post_status": {}}
        payload.update(extra)
        return client.post("/posts/", json=payload)

    def test_create_and_get_by_id_should_return_post(self, client: TestClient):
        """意图：创建帖子后，通过 /posts/id/{pid} 能查到该帖子（BizResponse 包装结构正确）。"""
        author = self._author(client)
        resp = self._create_post(client, author.uid)
        body1 = resp.json()
        assert resp.status_code == 200 and body1["code"] == 200

        pid = body1["data"]["pid"]
        resp = client.get(f"/posts/id/{pid}")
        body2 = resp.json()
        assert resp.status_code == 200 and body2["code"] == 200
        assert body2["data"]["pid"] == pid
        assert body2["data"]["post_content"]["title"] == "t"

    def test_get_by_id_should_return_404_when_not_found(self, client: TestClient):
        """意图：查询不存在的帖子，应返回 404 且 data 为 None。"""
        r = client.get("/posts/id/not-exist")
        assert r.status_code == 404
        body = r.json()
        assert body["code"] == 404
        assert body["data"] is None

    def test_get_by_author(self, client: TestClient):
        """意图：按作者查询帖子列表，返回分页结果。"""
        author = self._author(client)
        self._create_post(client, author.uid, title="t1")
        self._create_post(client, author.uid, title="t2")
        r = client.get(f"/posts/author/{author.uid}", params={"page": 0, "page_size": 10})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["total"] == 2

    def test_update_post_content(self, client: TestClient):
        """意图：作者更新帖子内容成功。"""
        author = self._author(client)
        created = self._create_post(client, author.uid, title="old", content="old c").json()
        pid = created["data"]["pid"]
        r = client.put(f"/posts/content/{pid}", params={"uid": author.uid}, json={"title": "new", "content": "new c"})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["post_content"]["title"] == "new"

    def test_update_post_visibility(self, client: TestClient):
        """意图：作者更新帖子可见性成功。"""
        author = self._author(client)
        created = self._create_post(client, author.uid).json()
        pid = created["data"]["pid"]
        r = client.put(f"/posts/visibility/{pid}", params={"uid": author.uid}, json={"visibility": 1})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["post_status"]["visibility"] == 1

    def test_publish_post(self, client: TestClient):
        """意图：发布草稿帖子成功（publish_status 0→1）。"""
        author = self._author(client)
        created = client.post(
            "/posts/",
            json={"author_id": author.uid, "title": "draft", "content": "draft c", "post_status": {"publish_status": 0}},
        ).json()
        pid = created["data"]["pid"]
        r = client.put(f"/posts/publish/{pid}", params={"uid": author.uid})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["post_status"]["publish_status"] == 1

    def test_soft_delete_post(self, client: TestClient):
        """意图：软删除帖子后，get_by_id 返回 404。"""
        author = self._author(client)
        created = self._create_post(client, author.uid).json()
        pid = created["data"]["pid"]
        r = client.delete(f"/posts/soft/{pid}", params={"uid": author.uid})
        assert r.status_code == 200
        r2 = client.get(f"/posts/id/{pid}")
        assert r2.status_code == 404

    def test_get_top_liked(self, client: TestClient):
        """意图：获取点赞榜接口返回 200（BizResponse 正确包装）。"""
        r = client.get("/posts/top/liked", params={"limit": 5})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200

    def test_get_top_commented(self, client: TestClient):
        """意图：获取评论榜接口返回 200。"""
        r = client.get("/posts/top/commented", params={"limit": 5})
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
