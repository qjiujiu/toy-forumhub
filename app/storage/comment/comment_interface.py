# app/storage/comment/comment_interface.py

from typing import Optional, List, Protocol

from app.schemas.comment import (
    CommentOnlyCreate,
    CommentOut,
    CommentAdminOut,
    BatchCommentsOut,
    BatchCommentsAdminOut,
    ReviewUpdate,
    StatusUpdate,
)


class ICommentRepository(Protocol):
    """
    评论仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源
    """

    # ---------- 创建 ----------

    def create_comment(self, data: CommentOnlyCreate) -> str:
        """
        创建评论（仅写入 comments 表）：
        - 返回新建评论的业务主键 cid
        - 评论内容（CommentContent）由业务层调用对应仓库创建
        """
        ...

    # ---------- 单条查询 ----------

    def get_comment_by_cid_for_user(self, cid: str) -> Optional[CommentOut]:
        """
        普通用户 / 前台访客查看单条评论：
        - 过滤软删除
        - 过滤折叠(status != FOLDED)
        - 过滤审核 REJECTED 的评论
        """
        ...

    def get_comment_by_cid_for_admin(self, cid: str) -> Optional[CommentAdminOut]:
        """
        管理员根据 cid 查看评论详情：
        - 不过滤软删除
        - 响应体包含作者信息、deleted_at 等（CommentAdminOut）
        """
        ...


    # ---------- 按root_id查询列表 ----------
    def list_comments_by_root_for_user(self, root_id: str, page: int | None = None, page_size: int | None = None) -> BatchCommentsOut:
        """
        用户视角：根据 root_id 获取整组对话（楼）里的所有评论
        - 过滤软删除 / 折叠 / REJECTED
        - 按时间顺序（或 _id 顺序）返回
        """
        ...

    # ---------- 按帖子查询列表 ----------

    def list_comments_by_post_for_user(
        self, post_id: str, page: int, page_size: int
    ) -> BatchCommentsOut:
        """
        普通用户 / 前台访客查看某帖子的评论列表：
        - 不含折叠
        - 不含软删除
        - 不含 REJECTED 评论
        """
        ...

    def list_comments_by_post_for_reviewer(
        self, post_id: str, page: int, page_size: int
    ) -> BatchCommentsAdminOut:
        """
        审核员查看某帖子的评论列表：
        - 看得到所有审核状态（PENDING / APPROVED / REJECTED）
        - 但看不到软删除（deleted_at IS NOT NULL）
        - 使用 CommentAdminOut（包含作者信息等）
        """
        ...

    def list_comments_by_post_for_admin(
        self, post_id: str, page: int, page_size: int
    ) -> BatchCommentsAdminOut:
        """
        管理员查看某帖子的评论列表：
        - 含软删除
        - 含折叠、REJECTED 等所有状态
        """
        ...

    # ---------- 审核 / 状态更新 ----------

    def update_review(self, cid: str, data: ReviewUpdate) -> bool:
        """
        更新评论审核状态（审核员 / 管理员）：
        - 更新 review_status
        - 同时更新 reviewed_at 为当前时间
        - 返回 True 表示更新成功，False 表示未找到
        """
        ...

    def update_status(self, cid: str, data: StatusUpdate) -> bool:
        """
        更新评论显示状态（正常 / 折叠）（管理员）：
        - 更新 status 字段
        """
        ...

    # ---------- 删除 ----------

    def soft_delete_comment(self, cid: str) -> bool:
        """
        软删除评论：
        - 设置 deleted_at 为当前时间
        """
        ...
    
    def restore_comment(self, cid: str) -> bool:
        """恢复软删除的评论（deleted_at 置为 NULL）"""
        ...

    def hard_delete_comment(self, cid: str) -> bool:
        """
        硬删除评论：
        - 直接删除 comments 表记录
        - CommentContent 等关联记录建议通过级联或业务层统一处理
        """
        ...

    # ---------- 更新点赞数与评论数 ----------
        
    def update_comment_count(self, cid: str, step: int = 1) -> Optional[int]:
        """评论的子评论数自增/自减（限制不小于 0）"""
        ...

    def update_like_count(self, cid: str, step: int = 1) -> Optional[int]:
        """评论点赞数自增/自减（限制不小于 0）"""
        ...