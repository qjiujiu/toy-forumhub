from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from app.schemas.user import UserOut

class FollowCreate(BaseModel):
    """
    创建关注
    """
    user_id: str               # 关注者 UID（也可以从 token 中取，按你业务）
    followed_user_id: str      # 被关注者 UID

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class FollowOut(BaseModel):
    """
    单条关注关系输出：
    - 用于创建关注后的返回
    - 查询用户是否关注某人
    - 显示关注列表中的单项
    """
    user_id: str               # 关注者 UID
    followed_user_id: str      # 被关注者 UID

    model_config = ConfigDict(from_attributes=True)


class FollowAdminOut(BaseModel):
    """
    单条关注关系输出：
    - 用于创建关注后的返回
    - 查询用户是否关注某人
    - 显示关注列表中的单项
    """
    user_id: str               # 关注者 UID
    followed_user_id: str      # 被关注者 UID
    deleted_at:  Optional[datetime] = None # 删除时间

    model_config = ConfigDict(from_attributes=True)

class FollowUserOut(BaseModel):
    """
    在关注列表 / 粉丝列表展示中，更实用的结构：
    - 返回对方用户的基础信息
    - 可扩展是否互关等逻辑
    """
    user: UserOut
    
    # 可扩展字段：是否已互相关注（可选，根据业务返回）
    is_mutual: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class BatchFollowsOut(BaseModel):
    """
    分页列表返回（关注列表/粉丝列表）
    - items: FollowUserOut 列表，表示对方用户的公开信息
    - total: 满足条件数量
    - count: 当前页数量
    """
    total: int
    count: int
    items: List[FollowUserOut]

    model_config = ConfigDict(from_attributes=True)



class FollowCancel(BaseModel):
    """
    取消关注（软删除）
    - 若接口路径包含用户 ID，可以不需要 body
    """
    user_id: str               # 关注者 UID
    followed_user_id: str      # 被关注者 UID

    model_config = ConfigDict(from_attributes=True, extra="forbid")
