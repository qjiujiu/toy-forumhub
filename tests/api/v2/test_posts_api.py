import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2 import posts as posts_api
from app.service.v2.post_svc import PostService

from app.storage.v2.mock.mock_post import (
    MockPostRepository,
)
from app.storage.v2.mock.mock_user import MockUserRepository
from app.schemas.v2.user import UserCreate


@pytest.fixture
def app():
    """ 
    这个函数会初始化 v2 的 Mock 仓库（内存实现），替换真实的存储层。

    说明：这里的帖子仓储采用“聚合仓储”风格：
    - 物理上可能是 `posts/post_contents/post_stats` 三表
    - 但对上层只暴露一个 `MockPostRepository`，把多表细节隐藏在对象内部

    补充说明:
        1. 这个函数顶部的 @pytest.fixture 是一个装饰器
        2. 带有 fixture 装饰器声明的函数是一个测试地基, 相当于把测试所需的基础资源固定下来, 能被测试类里面的每个测试函数使用
        3. 每个测试用例执行前，app fixture 会重新运行。意味着每个 test_ 函数拿到的都是一套干净、空内存仓库，保证了测试用例之间的互不干扰
    """

    # 由于没有数据库, 我们都把数据写在了内存里面：
    # - 此处的 `post_repo` 是一个“聚合仓库”, 数据表拆成了三份, 但是使用一个数据访问对象屏蔽底层实现细节
    # - 对外满足 IPostRepository 协议约束, 帖子的内容、统计信息也可以通过这个对象来做查询

    # NOTE: Python “鸭子类型”(Duck Typing)
    # - 无需显式继承某个父类/接口
    # - 只要对象提供了协议所需的方法, 即可被当作该协议类型使用
    user_repo = MockUserRepository()
    post_repo = MockPostRepository(user_repo=user_repo)

    api = FastAPI()
    # 这里的 app.state 是一个动态属性容器 State, 对它使用 . 成员运算符访问什么属性都不保持, 我们能往里面塞入任何东西
    api.state.user_repo = user_repo
    api.state.post_repo = post_repo

    # 主程序也有 include_router 这个操作, 这个操作相当于把 router 里面的函数挂在一个哈希表(i.e. 字典)上面
    api.include_router(posts_api.posts_router)

    def override_post_service() -> PostService:
        return PostService(post_repo, user_repo)

    # 平时 当某个路由 e.g. POST /posts/ 需要 PostService 时，FastAPI 会自动调用 posts_api.get_post_service 这个函数来创建一个连接了真实数据库的服务对象
    # 在正常运行的情况之下， FastAPI 在执行每一个请求前，会先去 dependency_overrides 这个字典查询当前这个依赖函数在不在这个字典里面,
    # 若在, 则取出来运行 (执行 key 指向的函数)
    # 下面的 dependency_overrides[posts_api.get_post_service] 本质上就是一个字典
    # 然后使用我们编写的 override_post_service 函数覆盖这个 post_api (i.e. app/api/v2/posts.py) 里面 get_post_service 函数,
    # 将其改为了 override_post_service, 相当于修改了一个字典某个key 对应的 value, key 名称就是原来函数的名称, value 就是原来函数的定义
    # 这是因为 Python 函数是可以在运行时通过赋值修改函数定义的!!!
    api.dependency_overrides[posts_api.get_post_service] = override_post_service
    return api


@pytest.fixture
def client(app):
    # 两个进程的通信可以看成 client-server 通信, 我们的FastAPI后端服务就是这个server,
    # 平时我们使用 postman 来做测试, postman 便是那个 client, 现在我们要在测试类里面添加使用一个对象来模拟 client
    return TestClient(app)


class TestPostsApiV2:
    def test_create_and_get_by_id_should_return_post(self, client: TestClient):
        """
        测试意图：创建帖子后，通过 `/posts/id/{pid}` 能够查到该帖子 (BizResponse 包装结构正确)
        """
        # 先在 mock user repo 里面创建作者（当前 service 未强校验 author_id，但这里提前准备，避免后续加校验导致用例失效）
        # client 里面拿出来的 app 就是上面定义的, app.state.user_repo 也是上述 app 里面定义的
        user_repo: MockUserRepository = client.app.state.user_repo
        author = user_repo.create_user(UserCreate(username="author", phone="111", password="pw"))
        payload = {
            "author_id": author.uid,
            "title": "t",
            "content": "c",
            "post_status": {},
        }
        resp = client.post("/posts/", json=payload)
        body1 = resp.json()
        assert resp.status_code == 200 and body1["code"] == 200

        pid = body1["data"]["pid"]

        # 使用 GET 方法查询新插入的帖子
        resp = client.get(f"/posts/id/{pid}")
        body2 = resp.json()

        # 验证状态码正确, 验证新插入的内容正确
        assert resp.status_code == 200 and body2["code"] == 200
        assert body2["data"]["pid"] == pid and body2["data"]["post_content"]["title"] == "t"

    def test_get_by_id_should_return_404_when_not_found(self, client: TestClient):
        """
        测试意图：查询不存在的帖子，应返回 404 并且 data 等于 None
        """
        r = client.get("/posts/id/not-exist")
        assert r.status_code == 404
        body = r.json()
        assert body["code"] == 404
        assert body["data"] is None
