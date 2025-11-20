from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import ( 
    UserCreate,
    UserOut,
    UserAllOut,
    UserDetailOut,
    BatchUsersOut,
    UserUpdate,
    AdminUserUpdate,
)
from app.storage.user.user_interface import IUserRepository
from app.core.exceptions import UserNotFound
from app.core.db import transaction
class SQLAlchemyUserRepository(IUserRepository):
    """
    使用 SQLAlchemy 实现的用户仓库
    业务层依赖 IUserRepository 接口，而不是这个具体实现
    """

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        """内部封装一个基础查询（过滤软删除）"""
        return self.db.query(User).filter(User.deleted_at.is_(None))

    def get_user_by_uid(self, uid: str) -> Optional[UserAllOut]:
        user = self._base_query().filter(User.uid == uid).first()
        return UserAllOut.model_validate(user) if user else None

    def get_user_detail_by_uid(self, uid: str) -> Optional[UserDetailOut]:
        """
        当前 UserDetailOut 仅继承 UserOut，没有额外字段，
        这里先按和 get_user_by_uid 一样的处理方式返回。
        将来你在 UserDetailOut 里加统计字段时，可以在这里做 join/聚合。
        """
        user = self._base_query().filter(User.uid == uid).first()
        return UserDetailOut.model_validate(user) if user else None

    def get_user_by_phone(self, phone: str) -> Optional[UserOut]:
        user = self._base_query().filter(User.phone == phone).first()
        return UserOut.model_validate(user) if user else None

    def get_users_by_username(self, username: str, page: int, page_size: int) -> BatchUsersOut:
        """
        根据用户名分页查询同名用户，返回 BatchUsersOut
        """
        base_q = (
            self._base_query()
            .filter(User.username == username)
            .order_by(User.created_at.desc())
        )

        total = base_q.count()

        users_orm = (
            base_q
            .offset(page * page_size)   # page 从 0 开始
            .limit(page_size)
            .all()
        )

        users_out = [UserOut.model_validate(u) for u in users_orm]

        return BatchUsersOut(
            total=total,
            count=len(users_out),
            users=users_out,
        )
    
    def get_batch_users(self, page: int, page_size: int) -> BatchUsersOut:
        """
        分页获取用户列表
        这里和你给的示例保持风格一致：page 视为从 0 开始
        - offset = page * page_size
        """
        base_q = self._base_query().order_by(User.created_at.desc())

        total = base_q.count()
        users_orm = (
            base_q
            .offset(page * page_size)   # 如果你想 1 开始，可以改为 (page - 1) * page_size
            .limit(page_size)
            .all()
        )

        # 把 ORM 对象转换为 Pydantic 模型
        users_out = [UserOut.model_validate(u) for u in users_orm]

        # 返回 BatchUsersOut（业务层/接口层如需 dict，可调用 .model_dump()）
        return BatchUsersOut(
            total=total,
            count=len(users_out),
            users=users_out,
        )

    def create_user(self, user_data: UserCreate) -> UserOut:
        """
        创建用户
        - 假定 user_data.password 已经是加密后的哈希
        - role/status 如果不传，使用数据库的默认值或枚举默认值
        """
        data = user_data.model_dump(exclude_none=True)

        user = User(**data)

        # 使用事务管理器
        with transaction(self.db):
            self.db.add(user)

        # 提交完成之后再 refresh，拿到最新状态（包括默认值等）
        self.db.refresh(user)

        return UserOut.model_validate(user)

    def update_user(self, uid: str, user_data: UserUpdate) -> Optional[UserOut]:
        """
        普通用户更新：
        - 只允许改 username/email/phone/avatar_url/bio
        """
        user = self._base_query().filter(User.uid == uid).first()
        if not user:
            raise UserNotFound(f"user {uid} not found")

        update_data = user_data.model_dump(exclude_none=True)

        with transaction(self.db):
            for field, value in update_data.items():
                setattr(user, field, value)
            user.updated_at = datetime.now(timezone(timedelta(hours=8)))

        self.db.refresh(user)
        return UserOut.model_validate(user)

    def admin_update_user(self, uid: str, user_data: AdminUserUpdate) -> Optional[UserOut]:
        """
        管理员更新：
        - 在普通更新基础上，允许修改 role/status
        """
        user = self._base_query().filter(User.uid == uid).first()
        if not user:
            raise UserNotFound(f"user {uid} not found")

        update_data = user_data.model_dump(exclude_none=True)

        with transaction(self.db):
            for field, value in update_data.items():
                setattr(user, field, value)
            user.updated_at = datetime.utcnow()

        self.db.refresh(user)
        return UserOut.model_validate(user)

    def update_password(self, uid: str, new_password_hash: str) -> bool:
        """
        修改密码：
        - new_password_hash 需在业务层先完成加密
        """
        user = self._base_query().filter(User.uid == uid).first()
        if not user:
            return False

        with transaction(self.db):
            user.password = new_password_hash
            user.updated_at = datetime.now(timezone(timedelta(hours=8)))

        self.db.refresh(user)
        return True

    def soft_delete_user(self, uid: str) -> bool:
        """
        软删除用户：
        - 实际上只是打上 deleted_at 时间戳
        """
        user = self._base_query().filter(User.uid == uid).first()
        if not user:
            raise UserNotFound(f"user {uid} not found")

        with transaction(self.db):
            user.deleted_at = datetime.now(timezone(timedelta(hours=8)))

        return True
    
    def hard_delete_user(self, uid: str) -> bool:
        """
        直接物理删除用户，不再保留记录
        注意：调用方应确保这是“可被硬删”的用户（如管理员确认）
        """
        # 包含已软删除用户一起查
        user = self.db.query(User).filter(User.uid == uid).first()
        if not user:
            raise UserNotFound(f"user {uid} not found")

        with transaction(self.db):
            self.db.delete(user)

        return True
