from typing import Optional, Protocol
from app.schemas.v2.post import PostOnlyCreate, PostOut, BatchPostsOut, PostDto


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