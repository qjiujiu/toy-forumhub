from typing import Optional, List, Protocol

from app.schemas.follow import (
    FollowCreate,
    FollowOut,
    FollowUserOut,
    BatchFollowsOut,
    FollowCancel,
)


class IFollowRepository(Protocol):
    """
    关注关系仓库接口协议（数据层抽象接口）
    业务层只依赖本接口，不依赖具体 SQLAlchemy 实现
    """

    def create_follow(self, data: FollowCreate) -> FollowOut:
        """
        创建关注关系：
        - 如果之前存在软删除记录，视为“重新关注”，会把 deleted_at 置空
        - 如果已经存在有效记录，可直接返回当前记录（是否视为错误交给业务层决定）
        """
        ...

    def cancel_follow(self, data: FollowCancel) -> bool:
        """
        取消关注（软删除）：
        - 给 deleted_at 赋当前时间
        - 返回是否成功取消（不存在有效记录则返回 False）
        """
        ...

    def get_follow(self, user_id: str, followed_user_id: str) -> Optional[FollowOut]:
        """
        获取一条“有效的”关注关系（deleted_at is NULL）
        """
        ...

    def is_following(self, user_id: str, followed_user_id: str) -> bool:
        """
        判断 user_id 是否正在关注 followed_user_id（软删除的不算）
        """
        ...


    def list_following(self, user_id: str, page: int, page_size: int) -> BatchFollowsOut:
        """
        获取用户的“关注列表”（我关注了谁）
        - user_id: 当前用户 UID
        - page: 页码（0 开始）
        - page_size: 每页数量
        - 返回 FollowUserOut 列表（对方用户信息 + 是否互关）
        """
        ...

    def list_followers(self, user_id: str, page: int, page_size: int) -> BatchFollowsOut:
        """
        获取用户的“粉丝列表”（谁关注了我）
        - user_id: 当前用户 UID
        - page: 页码（0 开始）
        - page_size: 每页数量
        - 返回 FollowUserOut 列表（对方用户信息 + 是否互关）
        """
        ...


    def hard_delete_all_by_user(self, user_id: str) -> int:
        """
        硬删除与某用户相关的所有关注记录（通常配合用户硬删除使用）
        - 包含 user_id / followed_user_id 两个方向
        - 返回删除条数
        """
        ...
