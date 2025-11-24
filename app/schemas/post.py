from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.models.post import PostVisibility, PostReviewStatus, PostPublishStatus

from app.schemas.post_content import PostContentOut
from app.schemas.post_stats import PostStatsOut

# 创建一篇帖子
class PostCreate(BaseModel):
    """
    创建帖子（业务上通常由作者自己调用）
    """
    author_id: str        # 作者ID
    title: str            # 标题
    content: str          # 正文内容
    visibility: Optional[PostVisibility] = PostVisibility.PUBLIC.value
    publish_status: Optional[PostPublishStatus] = PostPublishStatus.PUBLISHED.value

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class PostGet(BaseModel):
    current_user_id: str   # 当前访问者
    author_id: str         # 帖子作者

class PostOnlyCreate(BaseModel):
    """
    创建帖子（内部调用插入帖子表中）
    """ 
    author_id: str        # 作者ID
    visibility: Optional[PostVisibility] = PostVisibility.PUBLIC.value               # 可见性：默认所有人可见
    publish_status: Optional[PostPublishStatus] = PostPublishStatus.PUBLISHED.value  # 发布状态：默认发布


# 查看帖子
class PostOut(BaseModel):
    """
    对外返回的基础帖子信息
    - 不包含内容本身（PostContent 单独表）
    - 可作为列表项 / 基础详情使用
    """
    pid: str                        # 帖子业务主键
    author_id: str                  # 作者 UID
    post_content: PostContentOut    # 帖子内容
    post_stats: PostStatsOut        # 帖子统计数据

    visibility: int                 # 可见性（0:公开, 1:仅作者）
    publish_status: int             # 发布状态（0:草稿, 1:发布）
    review_status: PostReviewStatus             # 审核状态
    reviewed_at: Optional[datetime] = None      # 审核时间

    model_config = ConfigDict(from_attributes=True)

# 查看帖子的审核状态
class PostReviewOut(BaseModel):
    pid: str                                    # 帖子业务主键
    author_id: str                              # 作者 UID
    post_content: PostContentOut    # 帖子内容
    review_status: PostReviewStatus             # 审核状态
    reviewed_at: Optional[datetime] = None      # 审核时间

    model_config = ConfigDict(from_attributes=True)


class PostAdminOut(BaseModel):
    pid: str                        # 帖子业务主键
    author_id: str                  # 作者 UID
    post_content: PostContentOut    # 帖子内容
    post_stats: PostStatsOut        # 帖子统计数据
    review_status: PostReviewStatus             # 审核状态
    reviewed_at: Optional[datetime] = None      # 审核时间
    visibility: int        # 可见性（0:公开, 1:仅作者）
    publish_status: int    # 发布状态（0:草稿, 1:发布）
    deleted_at: Optional[datetime] = None    # 软删除时间戳
    
    model_config = ConfigDict(from_attributes=True)

class BatchPostsAdminOut(BaseModel):
    """
    帖子分页列表返回：
    - total: 满足条件的总数
    - count: 当前页返回的数量
    - items: 帖子审核列表
    """
    total: int
    count: int
    items: List[PostAdminOut]

    model_config = ConfigDict(from_attributes=True)

class BatchPostsReviewOut(BaseModel):
    """
    帖子分页列表返回：
    - total: 满足条件的总数
    - count: 当前页返回的数量
    - items: 帖子审核列表
    """
    total: int
    count: int
    items: List[PostReviewOut]

    model_config = ConfigDict(from_attributes=True)

class BatchPostsOut(BaseModel):
    """
    帖子分页列表返回：
    - total: 满足条件的总数
    - count: 当前页返回的数量
    - items: 帖子列表
    """
    total: int
    count: int
    items: List[PostOut]

    model_config = ConfigDict(from_attributes=True)


class PostUpdate(BaseModel):
    """
    作者更新帖子的可见性与发布状态
    - 帖子的可见性可从所有人可见到仅作者可见随意切换
    - 帖子的发布状态只可以由草稿到发布状态的转变（业务层限制）
    """
    visibility: Optional[PostVisibility] = None
    publish_status: Optional[PostPublishStatus] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PostReviewUpdate(BaseModel):
    """
    审核员 / 管理员更新帖子审核状态
    - 用于审核接口
    - 审核状态可以从待审切换到通过或者拒绝，不可以从通过或拒绝切换回待审（业务层限制）
    """
    review_status: Optional[PostReviewStatus] 
    # reviewed_at 一般由后端在逻辑里写当前时间，这里可以不用前端传
    # 但如果你想做回放 / 修复，也可以允许传：
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")
