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
from app.schemas.v2.post_stats import PostStatsDto


class IPostRepository(Protocol):
    """
    帖子数据层抽象协议（聚合仓储）

    物理上 posts / post_contents / post_stats 仍然是三张独立表，
    但本接口屏蔽多表细节，对外以"一个帖子聚合"的形式提供读写能力。
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
        创建帖子聚合：一次事务内写入 posts + post_contents + post_stats。
        - 三张表要么都写成功，要么都失败回滚（聚合内一致性）。
        - 返回完整的 PostOut（包含内容与统计）。
        """
        pass

    # ========== 查 ==========

    def get_by_pid(self, pid: str) -> Optional[PostOut]:
        """
        根据 pid 获取单篇帖子（包含内容和统计信息）
        - 通过多表联合查询返回完整 PostOut
        - 过滤已软删除的帖子（deleted_at IS NULL）
        - 如果 post_content 缺失（数据不一致），返回 None
        """
        pass

    def get_by_author(self, author_id: str, page: int = 0, page_size: int = 10, selector: str = "public") -> BatchPostsOut:
        """
        根据 author_id 获取该作者的帖子（分页）
        - selector="public": 只返回所有人可见的已发布帖子
        - selector="own":    返回作者自己的所有已发布帖子（含仅自己可见）
        - 过滤已软删除的帖子
        - 过滤 content 缺失的异常数据
        - 按 _id 倒序
        """
        pass

    def get_all(self, page: int = 0, page_size: int = 10) -> BatchPostsOut:
        """
        获取所有帖子（分页）
        - 过滤已软删除的帖子
        - 过滤 content 缺失的异常数据
        - 按 _id 倒序
        """
        pass

    def get_top_liked_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        """返回近 7 天点赞数 TopN 的帖子（包含标题 + 作者基础信息 + 计数）。"""
        pass

    def get_top_commented_with_posts(self, limit: int = 10) -> List[TopPostOut]:
        """返回近 7 天评论数 TopN 的帖子（包含标题 + 作者基础信息 + 计数）。"""
        pass

    # ========== 改 ==========

    def update(self, pid: str, data: PostDto) -> bool:
        """
        更新帖子状态字段
        - visibility: 可见性（0=公开, 1=仅作者）
        - publish_status: 发布状态（0=草稿, 1=已发布）
        - 业务逻辑应在业务层控制
        """
        ...

    def update_stats(self, pid: str, data: PostStatsDto) -> bool:
        """
        增量更新帖子统计字段（post_stats 表）
        - like_count: 点赞数增量（+1 或 -1）
        - comment_count: 评论数增量（+1 或 -1）
        - 计数不应被更新到负数
        - 返回是否更新成功
        """
        ...

    def update_content(self, pid: str, data: PostContentUpdate) -> bool:
        """
        更新帖子内容（post_contents 表）
        - PATCH 语义：只更新显式传入的字段
        - 返回是否更新成功
        """
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
