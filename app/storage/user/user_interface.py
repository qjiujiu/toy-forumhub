from typing import Optional, List, Protocol
from datetime import datetime

from app.schemas.user import (  
    UserCreate,
    UserOut,
    UserAllOut,
    UserDetailOut,
    BatchUsersOut,
    UserUpdate,
    AdminUserUpdate,
    BatchUsersAllOut,
    UserAllOut
)

class IUserRepository(Protocol):
    """
    用户仓库接口协议（数据层抽象接口）
    业务层依赖本接口，而不是具体实现，方便后续替换为不同数据源（MySQL/PG/Mongo 等）
    """

    def get_user_by_uid(self, uid: str) -> Optional[UserAllOut]:
        """根据业务主键 uid 查询用户（已过滤软删除）"""
        ...

    def get_user_detail_by_uid(self, uid: str) -> Optional[UserDetailOut]:
        """查询用户详情（预留聚合字段扩展，比如关注数/粉丝数/发帖数等）"""
        ...

    def get_user_by_phone(self, phone: str) -> Optional[UserOut]:
        """根据手机号查询用户"""
        ...

    def get_users_by_username(self, username: str, page: int, page_size: int) -> BatchUsersOut:
        """
        根据用户名查询同名用户（分页）
        page: 页码（0 开始）
        page_size: 每页数量
        """
        ...

    def get_batch_users(self, page: int, page_size: int) -> BatchUsersOut:
        """
        分页获取用户列表
        page: 页码（建议与你原例子一致，0 开始）
        page_size: 每页数量
        """
        ...

    def create_user(self, user_data: UserCreate) -> UserOut:
        """
        创建用户
        注意：此处假定 user_data.password 已经是哈希后的密码（业务层负责加密）
        """
        ...

    def update_user(self, uid: str, user_data: UserUpdate) -> Optional[UserOut]:
        """
        普通用户信息更新（不含角色/状态）
        返回更新后的用户信息，未找到返回 None
        """
        ...

    def admin_update_user(self, uid: str, user_data: AdminUserUpdate) -> Optional[UserOut]:
        """
        管理员更新用户信息（可以修改角色、状态）
        返回更新后的用户信息，未找到返回 None
        """
        ...

    def update_password(self, uid: str, new_password_hash: str) -> bool:
        """
        更新用户密码（假定传入的是哈希后的密码）
        返回是否更新成功
        """
        ...

    def soft_delete_user(self, uid: str) -> bool:
        """
        软删除用户（设置 deleted_at）
        返回是否删除成功
        """
        ...

    # 硬删除接口，一般只给管理员或后台任务用
    def hard_delete_user(self, uid: str) -> bool:
        """
        硬删除用户（真正从数据库中删除记录）
        返回是否删除成功
        """
        ...

    def admin_get_users(self, page: int, page_size: int) -> BatchUsersAllOut:
        ...
    
    def admin_get_user_by_uid(self, uid: str) -> Optional[UserAllOut]:
        ...

    def admin_get_users_by_username(self, username: str, page: int, page_size: int) -> BatchUsersAllOut:
        ...

    def admin_list_deleted_users(self, page: int, page_size: int) -> BatchUsersAllOut:
        ...

    def admin_list_abnormal_status_users(self, page: int, page_size: int) -> BatchUsersAllOut:
        ...