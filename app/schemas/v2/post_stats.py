from typing import List, Optional
from pydantic import BaseModel, ConfigDict



class PostStatsDto(BaseModel):
    """
    可用于更新帖子统计：
    - 通常在点赞 / 取消点赞、评论增加 / 删除时调用
    - 不对外暴露，供业务层使用
    """

    like_count: Optional[int] = None
    comment_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class PostStatsCreate(BaseModel):
    """
    创建帖子统计记录（通常在创建帖子时自动建立）
    - 一般不对外暴露接口
    """
    post_id: str
    post_stats : PostStatsDto

    model_config = ConfigDict(from_attributes=True, extra="forbid")

class PostStatsOut(BaseModel):
    """
    返回帖子统计信息：
    - 用于帖子详情
    - 用于帖子列表时附带统计信息
    """
    psid: str           # 统计记录业务主键
    post_id: str        # 对应帖子 PID
    
    post_stats: PostStatsDto

    model_config = ConfigDict(from_attributes=True)


class BatchPostStatsOut(BaseModel):
    """
    批量返回帖子统计（后台管理可能需要）
    """
    total: int
    count: int
    items: List[PostStatsOut]

    model_config = ConfigDict(from_attributes=True)

