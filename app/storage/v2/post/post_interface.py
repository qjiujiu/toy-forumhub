from typing import Optional, Protocol, List

from app.schemas.v2.post import (
    PostCreate,
    PostOnlyCreate,
    PostOut,
    BatchPostsOut,
    PostDto,
    TopPostOut,
)
from app.schemas.v2.post_content import PostContentUpdate


class IPostRepository(Protocol):
    """
    帖子数据层抽象协议
    只定义增删改查，不含业务逻辑
    """

    # ========== 增 ==========

    def create(self, data: PostOnlyCreate) -> str:
        """
        创建帖子记录
        - 只写入 posts 表
        - 返回新帖子的 pid
        """
        pass

    def create_post(self, data: PostCreate) -> PostOut:
        """
        创建帖子“聚合”（Aggregate）

        你现在的数据表仍然是三张：
        - posts：帖子状态/索引（author_id、visibility、publish_status、deleted_at 等）
        - post_contents：标题 + 正文（通常是大字段 TEXT）
        - post_stats：点赞/评论计数（高频更新字段）

        但对业务层/接口层而言，一个“帖子”是一个整体，所以我们把三表写入收敛到一个仓储方法里。

        知识点：为什么要在仓储里做这个事情？
        - 这是 Repository Pattern + Aggregate 的结合：上层只依赖一个仓储接口，避免出现 service 需要同时依赖 3 个 repo。
        - 事务（Transaction）应该覆盖“聚合内的一致性”：创建帖子时必须保证三张表要么都写成功，要么都失败回滚。
        """
        pass

    # ========== 查 ==========

    def get_by_pid(self, pid: str) -> Optional[PostOut]:
        """
        根据 pid 获取单篇帖子（包含内容和统计信息）
        - 通过多表联合查询返回完整 PostOut
        - 过滤已软删除的帖子（deleted_at IS NULL）
        """
        pass

    def get_by_author(self, author_id: str, page: int = 0, page_size: int = 10) -> BatchPostsOut:
        """
        根据 author_id 获取该作者的所有帖子（分页）
        - 过滤已软删除的帖子
        - 按 _id 倒序
        """
        pass

    def get_all(self, page: int = 0, page_size: int = 10) -> BatchPostsOut:
        """
        获取所有帖子（分页）
        - 过滤已软删除的帖子
        - 按 _id 倒序
        """
        pass

    # ========== 改 ==========

    def update(self, pid: str, data: PostDto) -> bool:
        """
        更新帖子状态字段
        - visibility: 可见性（0=公开, 1=仅作者）
        - publish_status: 发布状态（0=草稿, 1=已发布）
        - 业务逻辑应在业务层控制
        """
        pass

    def update_content(self, pid: str, data: PostContentUpdate) -> bool:
        """
        更新帖子内容（post_contents 表）

        说明：这里选择“PATCH 语义”而不是“PUT 语义”。
        - PATCH：只更新显式传入的字段（例如只改 title，不动 content）
        - PUT：通常代表全量覆盖

        我们使用 Pydantic 的 `model_dump(exclude_none=True)` 来实现 PATCH：
        - exclude_none=True 的含义是：值为 None 的字段不参与更新
        - 这能避免“请求里没传的字段被误清空”
        """
        pass

    # ========== 查（特定场景：热榜） ==========

    def get_top_liked_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        """返回近 7 天点赞数 TopN 的帖子（包含标题 + 作者基础信息 + 计数）。"""
        pass

    def get_top_commented_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        """返回近 7 天评论数 TopN 的帖子（包含标题 + 作者基础信息 + 计数）。"""
        pass

    # ========== 删 ==========

    def soft_delete(self, pid: str) -> bool:
        """
        软删除帖子
        - 将 deleted_at 字段设置为当前时间
        - 返回是否操作成功
        """
        pass

    def hard_delete(self, pid: str) -> bool:
        """
        硬删除帖子
        - 级联删除 post_content 和 post_stats（通过 cascade）
        - 返回是否操作成功
        """
        pass
