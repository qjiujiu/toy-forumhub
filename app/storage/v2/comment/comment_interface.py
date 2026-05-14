from typing import Optional, Protocol

from app.schemas.v2.comment import (
    CommentCreate,
    CommentOnlyCreate,
    CommentOut,
    BatchCommentsOut,
    StatusUpdate,
    CommentQueryDTO,
    CommentUpdate,
)


class ICommentRepository(Protocol):
    """
    评论数据层抽象协议（聚合仓储）

    物理上 comments / comment_contents 仍然是两张独立表，
    但本接口屏蔽多表细节，对外以"一个评论聚合"的形式提供读写能力。
    """

    def create(self, data: CommentOnlyCreate) -> str:
        """
        创建评论记录
        - 只写入 comments 表
        - 返回新评论的 cid
        """
        ...

    def create_comment(self, data: CommentCreate) -> CommentOut:
        """
        创建评论聚合：一次事务内写入 comments + comment_contents。
        - 两张表要么都写成功，要么都失败回滚。
        - 返回完整的 CommentOut（包含内容）。
        """
        ...

    def get_by_cid(self, cid: str) -> Optional[CommentOut]:
        """
        根据 cid 获取单条评论（包含内容）
        - 过滤已软删除的评论（deleted_at IS NULL）
        - 如果 comment_content 缺失（数据不一致），返回 None
        """
        ...

    def get_comments(
        self,
        query: CommentQueryDTO,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchCommentsOut:
        """
        根据条件查询评论列表（分页）
        - 过滤已软删除的评论
        - 过滤 content 缺失的异常数据
        - 按 _id 倒序
        """
        ...

    def update(self, cid: str, data: StatusUpdate) -> bool:
        ...

    def update_counters(self, cid: str, data: CommentUpdate) -> bool:
        ...

    def hard_delete(self, cid: str) -> bool:
        ...

    def soft_delete(self, cid: str) -> bool:
        ...
