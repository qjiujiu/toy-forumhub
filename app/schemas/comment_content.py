from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CommentContentCreate(BaseModel):
    """
    创建评论内容：
    - 业务层通常在创建 Comment 后立即创建 CommentContent
    """
    comment_id: str     # FK -> comments.cid
    content: str        # 评论正文（Markdown / 富文本均可）

    model_config = ConfigDict(from_attributes=True, extra="forbid")

# 评论区不能删除重发评论，不允许更新编辑评论
# class CommentContentUpdate(BaseModel):
#     """
#     更新评论内容：
#     - 允许修改 content（比如用户编辑评论）
#     """
#     content: Optional[str] = None  # 评论内容

#     model_config = ConfigDict(from_attributes=True, extra="forbid")


class CommentContentOut(BaseModel):
    """
    评论内容对外展示体：
    - 用于评论详情页，或评论列表中附带评论内容
    """
    ccid: str
    comment_id: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchCommentContentsOut(BaseModel):
    """
    批量返回评论内容（一般后台管理会用到）
    """
    total: int
    count: int
    items: List[CommentContentOut]

    model_config = ConfigDict(from_attributes=True)
