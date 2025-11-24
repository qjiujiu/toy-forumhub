# app/storage/post_stats/post_stats_interface.py

from typing import Optional, Protocol

from app.schemas.post_stats import (
    PostStatsCreate,
    PostStatsUpdate,
    PostStatsOut,
    BatchPostStatsOut,
)


class IPostStatsRepository(Protocol):
    """
    帖子统计仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源
    """

    def get_by_psid(self, psid: str) -> Optional[PostStatsOut]:
        """根据统计记录业务主键 psid 获取统计信息"""
        ...

    def get_by_post_id(self, post_id: str) -> Optional[PostStatsOut]:
        """
        根据帖子业务主键 post_id 获取统计信息
        - post_id 在表中是 UNIQUE，所以最多一条
        """
        ...

    def get_batch(self, page: int, page_size: int) -> BatchPostStatsOut:
        """
        分页获取帖子统计信息（一般用于后台管理）
        page: 页码（建议从 0 开始）
        page_size: 每页数量
        """
        ...

    def create(self, data: PostStatsCreate) -> PostStatsOut:
        """
        创建帖子统计记录
        - 通常在创建帖子时自动调用
        """
        ...

    def create_for_post(self, post_id: str) -> PostStatsOut:
        """
        为指定 post_id 初始化统计记录：
        - 不存在则创建 like_count=0, comment_count=0
        - 已存在则直接返回
        """
        ...

    def update_stats(self, post_id: str, data: PostStatsUpdate) -> Optional[PostStatsOut]:
        """
        根据 post_id 更新统计数据（整体更新）
        - 只更新非 None 字段
        - 未找到返回 None
        """
        ...

    def update_likes(self, post_id: str, step: int = 1) -> PostStatsOut:
        """
        点赞数自增 / 自减：
        - step 为正数表示 +N
        - step 为负数表示 -N（会限制不小于 0）
        """
        ...

    def update_comments(self, post_id: str, step: int = 1) -> PostStatsOut:
        """
        评论数自增 / 自减：
        - step 为正数表示 +N
        - step 为负数表示 -N（会限制不小于 0）
        """
        ...

    def delete_by_post_id(self, post_id: str) -> bool:
        """
        根据 post_id 硬删除统计记录
        - 返回是否删除成功
        """
        ...
