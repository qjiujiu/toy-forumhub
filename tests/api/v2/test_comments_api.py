import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2 import comments as comments_api
from app.service.v2.comment_svc import CommentService
from app.schemas.v2.post import PostCreate, PostDto

from tests.mock.mock_comment import MockCommentRepository
from tests.mock.mock_post import MockPostRepository
from tests.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate


@pytest.fixture
def app():
    """初始化 FastAPI 应用，使用 Mock 存储 + dependency_overrides 替换真实依赖。"""
    user_repo = MockUserRepository()
    post_repo = MockPostRepository(user_repo=user_repo)
    comment_repo = MockCommentRepository(post_repo=post_repo, user_repo=user_repo)

    # 预置用户和帖子数据
    for i in range(2):
        u = user_repo.create_user(UserCreate(username=f"user{i}", phone=f"1{i:09d}", password="pw"))
        post_repo.create_post(PostCreate(author_id=u.uid, title=f"post{i}", content=f"content{i}", post_status=PostDto()))

    api = FastAPI()
    api.state.user_repo = user_repo
    api.state.post_repo = post_repo
    api.state.comment_repo = comment_repo
    api.include_router(comments_api.comments_router)

    def override_comment_service() -> CommentService:
        return CommentService(comment_repo, post_repo, user_repo)

    api.dependency_overrides[comments_api.get_comment_service] = override_comment_service
    return api


@pytest.fixture
def client(app):
    return TestClient(app)


class TestCommentsApiV2:
    """测试 Comments API 路由层（基于 Mock 仓储 + TestClient）。"""

    def test_create_and_get_by_id(self, client: TestClient):
        """意图：创建评论后，通过 /comments/id/{cid} 能查到该评论。"""
        user_repo = client.app.state.user_repo
        post_repo = client.app.state.post_repo
        author = user_repo.list_users(page=0, page_size=1).users[0]
        post = post_repo.get_all(page=0, page_size=1).items[0]

        payload = {"post_id": post.pid, "author_id": author.uid, "content": "nice post!"}
        r = client.post("/comments/", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        cid = body["data"]["cid"]
        assert body["data"]["comment_content"]["content"] == "nice post!"

        r2 = client.get(f"/comments/id/{cid}")
        assert r2.status_code == 200
        assert r2.json()["data"]["cid"] == cid

    def test_get_by_id_not_found(self, client: TestClient):
        """意图：不存在的评论返回 404。"""
        r = client.get("/comments/id/not-exist")
        assert r.status_code == 404
        assert r.json()["data"] is None

    def test_delete_comment(self, client: TestClient):
        """意图：软删除评论后，get_by_id 返回 404。"""
        user_repo = client.app.state.user_repo
        post_repo = client.app.state.post_repo
        author = user_repo.list_users(page=0, page_size=1).users[0]
        post = post_repo.get_all(page=0, page_size=1).items[0]

        created = client.post(
            "/comments/", json={"post_id": post.pid, "author_id": author.uid, "content": "to delete"}
        ).json()
        cid = created["data"]["cid"]

        r = client.delete(f"/comments/id/{cid}")
        assert r.status_code == 200

        r2 = client.get(f"/comments/id/{cid}")
        assert r2.status_code == 404

    def test_get_post_by_comment_cid(self, client: TestClient):
        """意图：通过评论 cid 获取关联帖子。"""
        user_repo = client.app.state.user_repo
        post_repo = client.app.state.post_repo
        author = user_repo.list_users(page=0, page_size=1).users[0]
        post = post_repo.get_all(page=0, page_size=1).items[0]

        created = client.post(
            "/comments/", json={"post_id": post.pid, "author_id": author.uid, "content": "test"}
        ).json()
        cid = created["data"]["cid"]

        r = client.get(f"/comments/post-by-cid/{cid}")
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 200
        assert body["data"]["pid"] == post.pid

    def test_get_post_by_comment_cid_not_found(self, client: TestClient):
        """意图：不存在的评论 cid 查询帖子返回 404。"""
        r = client.get("/comments/post-by-cid/nonexistent")
        assert r.status_code == 404
