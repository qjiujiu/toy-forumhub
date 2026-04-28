from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.v2.post import PostVisibility, PostPublishStatus

from app.models.v2.post import PostVisibility, PostPublishStatus

from app.schemas.v2.post_content import PostContentOut
from app.schemas.v2.post_stats import PostStatsOut, PostStatsDto

class PostDto(BaseModel):
    visibility: Optional[PostVisibility] = None
    publish_status: Optional[PostPublishStatus] = None

# 创建一篇帖子
class PostCreate(BaseModel):
    """
    创建帖子（业务上通常由作者自己调用）
    """
    author_id: str        # 作者ID
    title: str            # 标题
    content: str          # 正文内容

    post_status: PostDto

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("title", "content")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title and content cannot be empty")
        return v.strip()

class PostGet(BaseModel):
    current_user_id: str   # 当前访问者
    author_id: str         # 帖子作者

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class PostOnlyCreate(BaseModel):
    """
    创建帖子（内部调用插入帖子表中）
    """ 
    author_id: str        # 作者ID
    post_status: PostDto  # 帖子发布状态和可见性

    model_config = ConfigDict(from_attributes=True, extra="forbid")


# 查看帖子
class PostOut(BaseModel):
    """
    对外返回的基础帖子信息
    - 不包含内容本身（PostContent 单独表）
    - 可作为列表项 / 基础详情使用
    """
    pid: str                        # 帖子业务主键
    author_id: str                  # 作者 UID
    post_status: PostDto            # 帖子的状态（发布状态和可见性）
    post_content: PostContentOut    # 帖子内容 
    post_stats: PostStatsDto        # 帖子统计数据 (点赞数和评论数)

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
    visibility: Optional[PostVisibility] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class TopPostAuthorOut(BaseModel):
    uid: str
    username: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TopPostOut(BaseModel):
    """
    专门用于热榜展示的轻量级返回值结构
    """
    pid: str                        # 帖子业务主键
    title: str                      # 帖子标题
    author: TopPostAuthorOut        # 作者基础信息
    post_stats: PostStatsDto        # 包含点赞数和评论数

    model_config = ConfigDict(from_attributes=True)

class TopPostsResponse(BaseModel):
    """
    热榜列表返回：
    - items: 热榜帖子列表
    """
    items: List[TopPostOut]

    model_config = ConfigDict(from_attributes=True)


