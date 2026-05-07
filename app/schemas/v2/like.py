from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.like import LikeTargetType  


class LikeCreate(BaseModel):
    """
    创建点赞：
    - 业务上通常由当前登录用户对某个帖子 / 评论点赞
    - 一个用户对同一 target_type + target_id 只能有一条有效点赞记录
    """
    user_id: str                          # 点赞用户 UID（FK -> users.uid）
    target_type: LikeTargetType           # 点赞目标类型（0: 帖子, 1: 评论）
    target_id: str                        # 点赞目标业务主键（帖子 pid / 评论 cid）

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class GetTargetLike(BaseModel):
    """
    获取目标类型点赞的请求体："某内容点赞用户列表"
    - 不包含软删除
    """
    target_type: LikeTargetType           # 目标类型（帖子/评论）
    target_id: str                        # 目标业务主键

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    
class GetUserLike(BaseModel):
    """
    获取用户点赞列表的请求体："某用户点赞列表"
    - 不包含软删除
    """
    target_type: LikeTargetType           # 目标类型（帖子/评论）
    user_id: str                          # 点赞用户 UID

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LikeDto(BaseModel):
    """
    通用点赞查询体：按非空字段动态组合过滤条件。
    例如：只传 user_id + target_type 等价于 GetUserLike，
         只传 target_type + target_id 等价于 GetTargetLike。
    - 不包含软删除（存储层自动过滤 deleted_at IS NULL）
    """
    user_id: Optional[str] = None
    target_type: Optional[LikeTargetType] = None
    target_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LikeCancel(BaseModel):
    """
    取消点赞：
    - 通常只需要 user_id + target_type + target_id 即可定位记录
    - 如果你接口是 DELETE /likes/{lid}，那也可以不用这个模型
    """
    user_id: str
    target_type: LikeTargetType
    target_id: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LikeOut(BaseModel):
    """
    对外返回的点赞基础信息：
    - 一般用于：查看我给哪些内容点过赞 / 某个内容被哪些人点赞等
    - 不包含 deleted_at（仅展示有效点赞）
    """
    lid: str                              # 点赞业务主键（UUID）
    user_id: str                          # 点赞用户 UID
    target_type: LikeTargetType           # 目标类型（帖子/评论）
    target_id: str                        # 目标业务主键
    created_at: datetime                  # 点赞时间
    updated_at: datetime                  # 最近一次更新点赞时间

    model_config = ConfigDict(from_attributes=True)


class BatchLikesOut(BaseModel):
    """
    点赞分页列表（普通场景）：
    - 用于 "某用户点赞列表" / "某内容点赞用户列表" 等
    """
    total: int
    count: int
    items: List[LikeOut]

    model_config = ConfigDict(from_attributes=True)
