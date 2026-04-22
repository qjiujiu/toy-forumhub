from typing import Dict, List, Optional, Union

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    AdminUserUpdate,
    UserOut,
    UserDetailOut,
    BatchUsersOut,
    UserPasswordUpdate,
    BatchUsersAllOut,
    UserAllOut
)
from app.schemas.user_stats import (
    UserStatsOut,
    UserStatsWithUserOut,
)
from app.storage.user.user_interface import IUserRepository
from app.storage.user_stats.user_stats_interface import IUserStatsRepository
from app.storage.follow.follow_interface import IFollowRepository

from app.core.logx import logger
from app.core.exceptions import UserNotFound, PasswordMismatchError

from app.core.security import hash_password, verify_password


class UserService:
    """
    用户服务类 - 面向对象封装
    
    将零散的函数封装成类，采用面向对象的编程思维。
    私有方法处理内部逻辑，公有方法暴露给外部调用。
    """
    
    def __init__(
        self,
        user_repo: IUserRepository,
        stats_repo: IUserStatsRepository,
        follow_repo: Optional[IFollowRepository] = None
    ):
        """
        初始化用户服务
        
        Args:
            user_repo: 用户仓储实例
            stats_repo: 用户统计仓储实例
            follow_repo: 关注仓储实例（可选，用于硬删除）
        """
        self._user_repo = user_repo
        self._stats_repo = stats_repo
        self._follow_repo = follow_repo
    
    # ============================== 私有方法 ==============================
    
    def _hash_password(self, password: str) -> str:
        """
        私有方法：对密码进行哈希处理
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        return hash_password(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        私有方法：验证密码是否匹配
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            密码是否匹配
        """
        return verify_password(plain_password, hashed_password)
    
    def _validate_user_exists(self, uid: str) -> None:
        """
        私有方法：校验用户是否存在，不存在则抛出异常
        
        Args:
            uid: 用户ID
            
        Raises:
            UserNotFound: 用户不存在
        """
        user = self._user_repo.get_user_by_uid(uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
    
    def _get_user_or_raise(self, uid: str) -> UserOut:
        """
        私有方法：获取用户或抛出异常
        
        Args:
            uid: 用户ID
            
        Returns:
            用户对象
            
        Raises:
            UserNotFound: 用户不存在
        """
        user = self._user_repo.get_user_by_uid(uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        return user
    
    def _log_operation(self, operation: str, details: str) -> None:
        """
        私有方法：记录操作日志
        
        Args:
            operation: 操作名称
            details: 详细信息
        """
        logger.info(f"[{operation}] {details}")
    
    # ============================== 公有方法 - 用户创建 ==============================
    
    def create_user(self, user_data: UserCreate, to_dict: bool = True) -> Union[Dict, UserOut]:
        """
        创建用户：
        1. 对明文密码做 Argon2 哈希
        2. 创建 User 记录（password 存储哈希）
        3. 初始化 UserStats 记录（following_count = 0, followers_count = 0）
        
        Args:
            user_data: 用户创建数据
            to_dict: 是否转换为字典
            
        Returns:
            用户信息（字典或UserOut对象）
        """
        # 1. 对密码进行哈希（如果允许第三方登录密码为空，要注意判断）
        if user_data.password:
            hashed = self._hash_password(user_data.password)
            user_data.password = hashed

        # 2. 创建用户记录
        new_user = self._user_repo.create_user(user_data)
        self._log_operation("CREATE_USER", f"Created user uid={new_user.uid}")

        # 3. 为用户创建统计记录
        self._stats_repo.create_for_user(new_user.uid)
        self._log_operation("CREATE_USER", f"Initialized statistics for user uid={new_user.uid}")

        return new_user.model_dump() if to_dict else new_user
    
    # ============================== 公有方法 - 用户查询 ==============================
    
    def get_batch_users(
        self,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True
    ) -> Union[Dict, BatchUsersOut]:
        """
        分页获取用户列表（不含统计信息）
        
        Args:
            page: 页码
            page_size: 每页数量
            to_dict: 是否转换为字典
            
        Returns:
            用户列表（字典或BatchUsersOut对象）
        """
        result = self._user_repo.get_batch_users(page=page, page_size=page_size)
        return result.model_dump() if to_dict else result
    
    def get_users_by_username(
        self,
        username: str,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True
    ) -> Union[Dict, BatchUsersOut]:
        """
        根据用户名分页查询同名用户
        
        Args:
            username: 用户名
            page: 页码
            page_size: 每页数量
            to_dict: 是否转换为字典
            
        Returns:
            用户列表（字典或BatchUsersOut对象）
        """
        result = self._user_repo.get_users_by_username(
            username=username,
            page=page,
            page_size=page_size,
        )
        return result.model_dump() if to_dict else result
    
    def get_user_by_uid(
        self,
        uid: str,
        to_dict: bool = True
    ) -> Optional[Union[Dict, UserOut]]:
        """
        根据 uid 获取用户基础信息
        
        Args:
            uid: 用户ID
            to_dict: 是否转换为字典
            
        Returns:
            用户信息（字典或UserOut对象）
            
        Raises:
            UserNotFound: 用户不存在
        """
        user = self._user_repo.get_user_by_uid(uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        return UserOut.model_validate(user).model_dump() if to_dict else user
    
    def get_user_profile(
        self,
        uid: str,
        to_dict: bool = True
    ) -> Optional[Union[Dict, UserStatsWithUserOut]]:
        """
        用户详情：User 信息 + 关注数/粉丝数
        这里直接用 UserStatsWithUserOut（由 stats_repo join user 拼出）
        
        Args:
            uid: 用户ID
            to_dict: 是否转换为字典
            
        Returns:
            用��详情（字典或UserStatsWithUserOut对象）
            
        Raises:
            UserNotFound: 用户不存在
        """
        profile = self._stats_repo.get_with_user_by_user_id(uid)
        if not profile:
            raise UserNotFound(f"user {uid} not found")
        return profile.model_dump() if to_dict else profile
    
    # ============================== 公有方法 - 用户更新 ==============================
    
    def update_user(
        self,
        uid: str,
        data: UserUpdate,
        to_dict: bool = True
    ) -> Optional[Union[Dict, UserOut]]:
        """
        普通用户更新自己的信息
        
        Args:
            uid: 用户ID
            data: 用户更新数据
            to_dict: 是否转换为字典
            
        Returns:
            更新后的用户信息（字典或UserOut对象）
        """
        updated = self._user_repo.update_user(uid, data)
        if not updated:
            return None
        return updated.model_dump() if to_dict else updated
    
    def admin_update_user(
        self,
        uid: str,
        data: AdminUserUpdate,
        to_dict: bool = True
    ) -> Optional[Union[Dict, UserOut]]:
        """
        管理员更新用户信息（包含角色/状态）
        
        Args:
            uid: 用户ID
            data: 管理员用户更新数据
            to_dict: 是否转换为字典
            
        Returns:
            更新后的用户信息（字典或UserOut对象）
        """
        updated = self._user_repo.admin_update_user(uid, data)
        if not updated:
            return None
        return updated.model_dump() if to_dict else updated
    
    def change_password(self, uid: str, data: UserPasswordUpdate) -> bool:
        """
        修改密码：
        - 业务层负责校验 old_password 是否正确（需要结合登录表/认证逻辑）
        - 这里仅负责调用仓库层 update_password
        
        Args:
            uid: 用户ID
            data: 密码更新数据
            
        Returns:
            是否修改成功
            
        Raises:
            UserNotFound: 用户不存在
            PasswordMismatchError: 密码不匹配
        """
        # 校验旧密码
        user = self._get_user_or_raise(uid)
        if not self._verify_password(data.old_password, user.password):
            raise PasswordMismatchError()

        # 对新密码进行哈希
        if data.new_password:
            hashed = self._hash_password(data.new_password)
            data.new_password = hashed

        return self._user_repo.update_password(uid, hashed)
    
    # ============================== 公有方法 - 用户删除 ==============================
    
    def soft_delete_user(self, uid: str) -> bool:
        """
        软删除用户（只标记 deleted_at）
        - 关联的 Follow / UserStats 可视业务决定是否保留或单独清理
        
        Args:
            uid: 用户ID
            
        Returns:
            是否删除成功
        """
        ok = self._user_repo.soft_delete_user(uid)
        if ok:
            self._log_operation("SOFT_DELETE", f"Soft deleted user uid={uid}")
        return ok
    
    def hard_delete_user(self, uid: str) -> bool:
        """
        硬删除用户，在数据表中以及设置用户的相关记录一并删除其中包含：
        1. 删除与该用户相关的所有关注记录
        2. 删除用户的统计记录
        3. 删除用户的基本信息记录
        4. 删除用户帖子记录
        5. 删除用户的点赞记录
        6. 删除用户的评论记录
        
        注意：删除用户的点赞，评论以及关注记录的时, 涉及及count字段的变化，但不需要更新相关的 count 字段，
        用户允许关注一个已注销的用户，用户可以选择取关，这样就会有count字段的变化
        
        Args:
            uid: 用户ID
            
        Returns:
            是否删除成功
        """
        ok = self._user_repo.hard_delete_user(uid)
        if ok:
            self._log_operation("HARD_DELETE", f"Hard deleted user uid={uid}")
        return ok
    
    # ============================== 公有方法 - 管理员操作 ==============================
    
    def admin_get_users(
        self,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True,
    ) -> Union[Dict, BatchUsersAllOut]:
        """
        管理员：分页查看所有用户（包含软删）
        
        Args:
            page: 页码
            page_size: 每页数量
            to_dict: 是否转换为字典
            
        Returns:
            用户列表（字典或BatchUsersAllOut对象）
        """
        result = self._user_repo.admin_get_users(
            page=page,
            page_size=page_size,
        )

        self._log_operation(
            "ADMIN",
            f"list all users page={page}, page_size={page_size}, count={result.count}"
        )

        return result.model_dump() if to_dict else result
    
    def admin_get_user_by_uid(
        self,
        uid: str,
        to_dict: bool = True,
    ) -> Union[Dict, UserAllOut]:
        """
        管理员根据 uid 获取用户详情：
        - 不过滤软删除（数据层已实现 admin_get_user_by_uid）
        - 响应体为 UserAllOut（包含更多字段）
        
        Args:
            uid: 用户ID
            to_dict: 是否转换为字典
            
        Returns:
            用户详情（字典或UserAllOut对象）
            
        Raises:
            UserNotFound: 用户不存在
        """
        user = self._user_repo.admin_get_user_by_uid(uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")

        self._log_operation("ADMIN", f"get user uid={uid}")
        return user.model_dump() if to_dict else user
    
    def admin_get_users_by_username(
        self,
        username: str,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True,
    ) -> Union[Dict, BatchUsersAllOut]:
        """
        管理员根据用户名分页查询用户：
        - 不过滤软删除
        - 返回 BatchUsersAllOut
        
        Args:
            username: 用户名
            page: 页码
            page_size: 每页数量
            to_dict: 是否转换为字典
            
        Returns:
            用户列表（字典或BatchUsersAllOut对象）
        """
        result = self._user_repo.admin_get_users_by_username(
            username=username,
            page=page,
            page_size=page_size,
        )

        self._log_operation(
            "ADMIN",
            f"get users by username='{username}', "
            f"page={page}, page_size={page_size}, count={result.count}"
        )

        return result.model_dump() if to_dict else result
    
    def admin_list_deleted_users(
        self,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True,
    ) -> Union[Dict, BatchUsersAllOut]:
        """
        管理员查看所有软删除用户：
        - 只查 deleted_at IS NOT NULL
        - 返回 BatchUsersAllOut
        
        Args:
            page: 页码
            page_size: 每页数量
            to_dict: 是否转换为字典
            
        Returns:
            用户列表（字典或BatchUsersAllOut对象）
        """
        result = self._user_repo.admin_list_deleted_users(
            page=page,
            page_size=page_size,
        )

        self._log_operation(
            "ADMIN",
            f"list deleted users page={page}, "
            f"page_size={page_size}, count={result.count}"
        )

        return result.model_dump() if to_dict else result
    
    def admin_list_abnormal_status_users(
        self,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True,
    ) -> Union[Dict, BatchUsersAllOut]:
        """
        管理员查看异常状态用户：
        - "异常状态"的定义由数据层决定（例如 status = 1/2）
        - 返回 BatchUsersAllOut
        
        Args:
            page: 页码
            page_size: 每页数量
            to_dict: 是否转换为字典
            
        Returns:
            用户列表（字典或BatchUsersAllOut对象）
        """
        result = self._user_repo.admin_list_abnormal_status_users(
            page=page,
            page_size=page_size,
        )

        self._log_operation(
            "ADMIN",
            f"list abnormal status users page={page}, "
            f"page_size={page_size}, count={result.count}"
        )

        return result.model_dump() if to_dict else result