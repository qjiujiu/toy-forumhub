from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PostContentCreate(BaseModel):
    """
    创建帖子内容：
    - 一般在创建帖子(Post)之后调用，也可以在业务层封装成“创建帖子 + 内容”一步完成
    """
    post_id: str          # 对应 posts.pid
    title: str            # 标题
    content: str          # 正文内容（富文本/Markdown 视前端而定）

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PostContentUpdate(BaseModel):
    """
    更新帖子内容：
    - 通常允许修改 title / content
    """
    title: Optional[str] = None
    content: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PostContentOut(BaseModel):
    """
    对外返回的帖子内容：
    - 可用于帖子详情页
    - pcid 是内容表自己的业务主键
    """
    pcid: str
    post_id: str
    title: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class BatchPostContentsOut(BaseModel):
    """
    如果你有按条件批量查询内容（一般后台管理用），可以用这个分页结构
    """
    total: int
    count: int
    items: List[PostContentOut]

    model_config = ConfigDict(from_attributes=True)
