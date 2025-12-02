from typing import Optional, List, Protocol

from app.schemas.comment_content import (
    CommentContentCreate,
    CommentContentOut,
    BatchCommentContentsOut,
)


class ICommentContentRepository(Protocol):
    """
    评论内容仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源
    """


    def get_by_ccid(self, ccid: str) -> Optional[CommentContentOut]:
        """根据业务主键 ccid 查询评论内容"""
        ...

    def get_by_comment_id(self, comment_id: str) -> Optional[CommentContentOut]:
        """根据 comment_id（FK -> comments.cid）查询评论内容"""
        ...


    def list_by_comment_ids(self, comment_ids: List[str]) -> List[CommentContentOut]:
        """
        根据一组 comment_id 批量查询评论内容
        - 常用于：一次性拿多个评论的内容
        """
        ...

    def get_batch(self, page: int, page_size: int) -> BatchCommentContentsOut:
        """
        分页查询评论内容（一般用于后台管理）
        """
        ...


    def create(self, data: CommentContentCreate) -> CommentContentOut:
        """
        创建一条评论内容记录
        """
        ...

    def hard_delete_by_ccid(self, ccid: str) -> bool:
        """
        根据 ccid 物理删除评论内容
        - 返回 True 表示删除成功，False 表示未找到
        """
        ...

    def hard_delete_by_comment_id(self, comment_id: str) -> bool:
        """
        根据 comment_id 物理删除评论内容
        - 一般用于删除整条评论时一并删除内容
        - 返回 True 表示至少删了一条，False 表示没有找到记录
        """
        ...
