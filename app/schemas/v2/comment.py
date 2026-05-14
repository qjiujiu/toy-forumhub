from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.v2.comment import CommentStatus, ReviewStatus

from app.schemas.v2.comment_content import CommentContentOut

class CommentDto(BaseModel):
    """
    评论数据传输对象（DTO），包含评论的基本信息和作者信息等。
    - 主要用于内部服务之间的数据传输，外部接口建议使用 CommentOut
    """
    cid: str                      # 评论业务主键（UUID）
    post_id: str                  # 所属帖子 PID
    author_id: str                # 评论作者 UID
    comment_content: CommentContentOut  # 评论具体内容
    parent_id: Optional[str] = None     # 父评论 CID
    root_id: Optional[str] = None       # 顶级评论 CID

    comment_count: int            # 该评论的子评论数（楼中楼数量）
    like_count: int               # 点赞数

    status: CommentStatus         # 评论状态（正常/折叠）
    review_status: ReviewStatus   # 审核状态（待审/通过/拒绝）

    reviewed_at: Optional[datetime] = None   # 审核时间
    deleted_at: Optional[datetime] = None   # 软删除时间戳

class CommentQueryDTO(BaseModel):
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    author_id: Optional[str] = None
    post_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")



class CommentCreate(BaseModel):
    """
    创建评论（业务上通常由用户自己调用）：
    """
    post_id: str                  # 所属帖子 PID（FK -> posts.pid）
    author_id: str                # 评论作者 UID（FK -> users.uid）
    content: str                  # 评论内容，后续插入评论内容表中
    parent_id: Optional[str] = None   # 父评论 CID（首层评论时为 None）
    root_id: Optional[str] = None     # 顶级评论 CID（首层评论可等于自身，业务层可补）

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class CommentOnlyCreate(BaseModel):
    """
    创建评论（仅限评论表内部调用）：
    """
    post_id: str                  # 所属帖子 PID（FK -> posts.pid）
    author_id: str                # 评论作者 UID（FK -> users.uid）
    
    like_count: int = 0               # 点赞数（默认0）
    comment_count: int = 0            # 评论数（默认0）
    status: CommentStatus = CommentStatus.NORMAL.value          # 评论状态（默认正常）
    review_status: ReviewStatus = ReviewStatus.APPROVED.value   # 审核状态（默认通过）

    parent_id: Optional[str] = None   # 父评论 CID（首层评论时为 None）
    root_id: Optional[str] = None     # 顶级评论 CID（首层评论可等于自身，业务层可补）
    

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class CommentUpdate(BaseModel):
    like_count: Optional[int] = None
    comment_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")




class StatusUpdate(BaseModel):
    """
    审核评论（审核员）：
    """
    status: Optional[CommentStatus] = None
    review_status: Optional[ReviewStatus] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class CountUpdate(BaseModel):
    comment_count: int            # 该评论的子评论数（楼中楼数量）
    like_count: int               # 点赞数

class CommentOut(BaseModel):
    """
    对外返回的评论基础信息：
    - 不包含正文内容（正文在 CommentContent 表）
    - 常用于评论列表 / 详情
    """
    cid: str                      # 评论业务主键（UUID）
    post_id: str                  # 所属帖子 PID
    author_id: str                # 评论作者 UID
    comment_content: CommentContentOut  # 评论具体内容
    parent_id: Optional[str] = None     # 父评论 CID
    root_id: Optional[str] = None       # 顶级评论 CID

    comment_count: int            # 该评论的子评论数（楼中楼数量）
    like_count: int               # 点赞数

    status: CommentStatus         # 评论状态（正常/折叠）
    review_status: ReviewStatus   # 审核状态（待审/通过/拒绝）

    reviewed_at: Optional[datetime] = None   # 审核时间
    deleted_at: Optional[datetime] = None   # 软删除时间戳

    model_config = ConfigDict(from_attributes=True)


class BatchCommentsOut(BaseModel):
    """
    评论分页列表返回结构：
    - total: 满足条件的总评论数
    - count: 当前页的评论条数
    - items: 当前页的评论列表
    """
    total: int
    count: int
    items: List[CommentOut]

    model_config = ConfigDict(from_attributes=True)