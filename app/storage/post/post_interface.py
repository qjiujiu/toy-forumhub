# app/storage/post/post_interface.py

from typing import Optional, Protocol

from app.schemas.post import (
    PostOnlyCreate,
    PostOut,
    PostReviewOut,
    BatchPostsOut,
    PostUpdate,
    PostReviewUpdate,
    BatchPostsReviewOut,
    PostAdminOut,
    BatchPostsAdminOut,
    PostGet,
)


class IPostRepository(Protocol):
    """
    帖子仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源
    """

    def create_post(self, data: PostOnlyCreate) -> str:
        """
        创建帖子（仅写 posts 表，不写内容表、不写统计表）
        - 返回新帖子的业务主键 pid
        """
        ...

    # 通过帖子id查看帖子，通常是检索查看，所以使用的是访客查询_viewer_query方法
    def viewer_get_post_by_pid(self, pid: str) -> Optional[PostOut]:
        ...

    # 用户通过帖子id查看帖子, 使用作者查询_author_query方法
    def author_get_post_by_pid(self, pid: str, author_id: str) -> Optional[PostOut]:
        ...

    def get_post_review_by_pid(self, pid: str) -> Optional[PostReviewOut]:
        """
        根据帖子业务主键 pid 获取审核信息：
        - 包含帖子内容 + 审核状态 + 审核时间
        - 已过滤软删除
        """
        ...
    def get_post_reviews_by_author(self, author_id: str, page: int, page_size: int,) -> BatchPostsReviewOut:
        """
        通过作者 ID 查看该作者的所有帖子（包含所有审核状态）：
        - 过滤 deleted_at
        - 不过滤 review_status
        - 按 _id 倒序（可改为按创建时间）
        """
        ...

    def list_pending_review_posts(self, page: int, page_size: int,) -> BatchPostsReviewOut:
        """
        查看所有待审帖子（管理员用）：
        - 只查 review_status = PENDING
        - 过滤 deleted_at
        """
        ...

    def get_batch_posts(self, page: int, page_size: int) -> BatchPostsOut:
        """
        分页获取帖子列表（通常为公开帖子）
        - 当前实现：只过滤 deleted_at IS NULL，其它条件由业务层控制或后续扩展
        - page: 页码（建议从 0 开始）
        - page_size: 每页数量
        """
        ...
    
    def get_posts_by_author(self, data: PostGet, page: int, page_size: int,) -> BatchPostsOut:
        """
        根据作者 ID 分页获取该作者的帖子列表
        - 响应体为 BatchPostsOut
        """
        ...

    def update_post(self, pid: str, data: PostUpdate) -> bool:
        """
        作者更新帖子的可见性 / 发布状态
        - 返回是否更新成功
        """
        ...

    def update_review(self, pid: str, data: PostReviewUpdate) -> bool:
        """
        审核员 / 管理员更新帖子审核状态
        - 返回是否更新成功
        """
        ...

    def soft_delete_post(self, pid: str) -> bool:
        """
        软删除帖子（设置 deleted_at）
        - 返回是否操作成功
        """
        ...

    #----------------------------------- 管理员用 ----------------------------------------
    def hard_delete_post(self, pid: str) -> bool:
        """
        硬删除帖子记录（直接从 posts 表物理删除）
        - 注意：关联的内容、统计等推荐在业务层或外键级联中一起处理
        - 返回是否删除成功
        """
        ...
    
    # 通过帖子id获取帖子信息
    def admin_get_post_by_pid(self, pid: str) -> Optional[PostAdminOut]:
        """
        管理员根据帖子 ID 获取帖子详情：
        - 不过滤 deleted_at（软删除也能看）
        """
        ...
    
    # 查看所有帖子（含软删）
    def admin_list_all_posts(self, page: int, page_size: int) -> BatchPostsAdminOut:
        ...
    
    # 查看所有软删除帖子
    def admin_list_deleted_posts(self, page: int, page_size: int) -> BatchPostsAdminOut:
        ...

    # 通过作者 ID 查看所有帖子（含软删）
    def admin_list_posts_by_author(self, author_id: str, page: int, page_size: int) -> BatchPostsAdminOut:
        ...
