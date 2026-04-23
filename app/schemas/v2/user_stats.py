from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.v2.user import UserOut

class UserStatsDto(BaseModel):
    """
    单条用户统计信息输出：
    - 展示用户的关注数、粉丝数
    - 常用于 GET /users/{uid}/statistics
    """
    following_count: int
    followers_count: int

    model_config = ConfigDict(from_attributes=True)


class UserStatsWithUserOut(BaseModel):
    """
    用于用户主页 / 用户详情展示：
    - 返回用户信息（UserOut） + 关注/粉丝数
    """
    user_info: UserOut
    user_stats: UserStatsDto

    model_config = ConfigDict(from_attributes=True)

# 通常用不上
class UserStatsUpdate(BaseModel):
    """
    用于服务层内部更新统计数据。
    - 注意：通常不会暴露给前端接口。
    """
    user_stats: UserStatsDto

    model_config = ConfigDict(from_attributes=True, extra="forbid")
