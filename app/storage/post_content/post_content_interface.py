# app/storage/post_content/post_content_interface.py

from typing import Optional, List, Protocol

from app.schemas.post_content import (
    PostContentCreate,
    PostContentUpdate,
    PostContentOut,
    BatchPostContentsOut,
)


class IPostContentRepository(Protocol):
    """
    帖子内容仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源
    """

    def get_by_pcid(self, pcid: str) -> Optional[PostContentOut]:
        """根据内容业务主键 pcid 获取帖子内容"""
        ...

    def get_by_post_id(self, post_id: str) -> Optional[PostContentOut]:
        """
        根据帖子业务主键 post_id 获取帖子内容
        - 由于 post_id 在表中是 UNIQUE，所以只会返回一条或 None
        """
        ...

    def get_batch(self, page: int, page_size: int) -> BatchPostContentsOut:
        """
        分页获取帖子内容（一般用于后台管理）
        page: 页码（建议从 0 开始）
        page_size: 每页数量
        """
        ...

    def create(self, data: PostContentCreate) -> PostContentOut:
        """
        创建帖子内容
        - 通常在帖子创建之后调用
        """
        ...

    def update_by_pcid(self, pcid: str, data: PostContentUpdate) -> Optional[PostContentOut]:
        """
        根据 pcid 更新帖子内容
        - 只更新非 None 字段
        - 未找到返回 None
        """
        ...

    def delete_by_pcid(self, pcid: str) -> bool:
        """
        根据 pcid 硬删除帖子内容
        - 返回是否删除成功
        """
        ...
