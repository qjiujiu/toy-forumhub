from typing import Optional, Protocol

from app.models.v2.user import UserRole, UserStatus
from app.schemas.v2.user import UserOut, BatchUsersOut
from app.schemas.v2.user_req import UserPatch

from app.schemas.v2.user_stats import UserStatsDto, UserStatsWithUserOut


class IUserRepository(Protocol):
    """
    用户仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源（MySQL/PG/Mongo 等）
    """

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        """
        根据 uid 或 phone 查询用户
        通过传参控制通过不同字段查找
        """
        ...

    def list_users(
        self,
        username: Optional[str] = None,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        """
        根据用户名查询或分页获取用户列表
        username 为 None 时获取所有用户
        """
        ...

    def create_user(self, username: str, phone: str, hashed_password: str) -> UserOut:
        """
        创建用户 (包括用户的统计信息也会被默认创建)
        """
        ...

    # 计信息（聚合能力）
    # 注意：物理存储方面,  user_stats 仍然是一张独立的数据表, 这里“统计表的访问”并入 UserRepository 主要原因是为了向业务层屏蔽细节
    # - repo 职责是屏蔽底层“分表实现细节”，避免 service/api 依赖多个 repo, 数据层要做的就是把底层为了性能而分表设计的数据表, 在逻辑上聚起来
    # - 对于业务层而言，“用户”是一个整体 (Aggregate), 关注数/粉丝数属于用户的聚合内数据,
    # 这一点 PostRepository 合并 post_contents/post_stats 其实是同一个思路。

    def get_stats(self, user_id: str) -> UserStatsDto:
        """获取用户统计

        - 对业务层来说：用户一旦被创建出来，就应该必然拥有一份统计信息（默认 0/0）。
            Post 聚合的思路也是如初一撤的: 帖子创建出来就应该同时拥有内容、统计信息。

        - 对数据访问层来说：repo 要做的是“聚合写入”来保证不变量，而不是在读路径上悄悄补数据。
          如果某个 user_id 查询不到统计记录，这是属于数据不一致 (例如历史数据缺失/迁移漏跑) 问题, 理论上不应该发生
          更合适的处理是：
          - 直接让调用方感知到异常（例如抛出数据不一致错误）
          - 通过显式的 backfill(兜底) 脚本修复数据
        """
        ...

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> Optional[UserStatsDto]:
        """增量更新关注/粉丝计数（计数不应被更新到负数）。"""
        ...

    def get_user_profile(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        """返回用户详情：UserOut + UserStatsDto（用于个人主页/详情页）。"""
        ...


    # 设计取舍: 没有一种设计是完美的, 在做写服务的时候通常会有两种取舍:
    #   - 一种是自上而下, “接口层-业务层-数据层” 全部修改一遍, 坏处自然就是改动量很大
    #   - 另外一种做法是让 repo 尽可能保持“原始 CRUD”语义, 接口命名都是 find/list/create/update/delete 这类非常直观的命名
    # 然后再按 “用户意图”拆分 CRUD, 比如 "用户更新信息这个场景的"（update_user_info/reset_password/soft_delete/set_role/set_status）
    # 本质都是更新交给 service 层编排, 但是 repo  update 不可以无边界的：我们需要使用 `UserPatch` (分类型 patch) 来约束可更新字段。
    # 为什么还要区分 patch 类型？
    # - 如果只有一个 `dict`, 或者万能 DTO，普通更新很容易误改敏感字段（role/status/password/deleted_at）。
    # - 区分 patch 类型相当于把“权限边界/字段边界”写进类型系统，减少误用。

    def update_user(self, uid: str, patch: UserPatch) -> Optional[UserOut]:
        """通用更新入口。

        - PATCH 语义：只更新 patch 里“显式传入”的字段。
        - 返回更新后的 UserOut；如果用户不存在（或不可见），返回 None。
        """
        ...

    def delete_user(self, uid: str) -> bool:
        """
        硬删除用户
        """
        ...

    def get_password(self, uid: str) -> Optional[str]:
        """
        获取用户密码（用于验证）
        """
        ...
