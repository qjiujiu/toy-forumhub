from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.db import transaction
from app.storage.v2.user.user_interface import IUserRepository
from app.models.v2.user import User, UserRole, UserStatus
from app.models.v2.user_stats import UserStats
from app.schemas.v2.user_req import UserPatch, UserInfoPatch, UserAdminPatch, UserPasswordPatch
from app.schemas.v2.user_stats import UserStatsDto, UserStatsWithUserOut
from app.schemas.v2.user import (
    UserInfoDto,
    UserTimeDto,
    UserOut,
    BatchUsersOut,
)


def _to_user_out(user: User) -> UserOut:
    return UserOut(
        uid=user.uid,
        user_info=UserInfoDto.model_validate(user),
        user_data=UserTimeDto.model_validate(user),
    )


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(User).filter(
            User.deleted_at.is_(None),
            User.status == 0,
        )

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        if uid:
            user = self._base_query().filter(User.uid == uid).first()
        elif phone:
            user = self._base_query().filter(User.phone == phone).first()
        else:
            return None
        return _to_user_out(user) if user else None

    def list_users(
        self,
        username: Optional[str] = None,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        base_q = self._base_query()
        if username:
            base_q = base_q.filter(User.username == username)
        base_q = base_q.order_by(User.created_at.desc())

        total = base_q.count()
        users_orm = base_q.offset(page * page_size).limit(page_size).all()
        users_out = [_to_user_out(u) for u in users_orm]

        return BatchUsersOut(
            total=total,
            count=len(users_out),
            users=users_out,
        )

    def create_user(self, username: str, phone: str, hashed_password: str) -> UserOut:
        """创建用户聚合：一次事务内写入 users + user_stats。

        物理存储仍然是两张表：
        - users：用户静态信息 + 时间字段
        - user_stats：关注数/粉丝数（高频更新字段）

        但对业务层来说，“创建用户”是一件事情；repo 负责屏蔽分表细节。

        知识点：为什么要在同一个事务里写两张表？
        - 聚合内一致性（Aggregate Consistency）：
          用户创建成功后，默认应该有一条统计记录（0/0）。
        - 如果分两次写，会出现“用户存在但统计缺失”的中间态，后续读写需要大量 if/兜底。
        """

        user = User(
            username=username,
            phone=phone,
            password=hashed_password,
            role=UserRole.NORMAL_USER.value,
            status=UserStatus.NORMAL.value,
        )

        # 注意：User.uid 的默认值是 uuid lambda，因此在对象创建时就已经可用。
        # 这让我们能直接创建 UserStats 并在同一事务里落库。
        stats = UserStats(user_id=user.uid, following_count=0, followers_count=0)

        with transaction(self.db):
            self.db.add_all([user, stats])

        self.db.refresh(user)
        return _to_user_out(user)

    # 通用更新入口（CRUD + 通用 update
    def update_user(self, uid: str, patch: UserPatch) -> Optional[UserOut]:
        user = self.db.query(User).filter(User.uid == uid, User.deleted_at.is_(None)).first()
        if not user: return None

        update_data = patch.model_dump(exclude_unset=True)
        with transaction(self.db):
            for field, value in update_data.items():
                setattr(user, field, value)

            user.updated_at = datetime.now(timezone(timedelta(hours=8)))
        self.db.refresh(user)
        return _to_user_out(user)

    def delete_user(self, uid: str) -> bool:
        user = self.db.query(User).filter(User.uid == uid).first()
        if not user:
            return False
        with transaction(self.db):
            self.db.delete(user)
        return True

    def get_password(self, uid: str) -> Optional[str]:
        user = self._base_query().filter(User.uid == uid).first()
        return user.password if user else None

    # 聚合能力：user_stats
    def _get_stats_orm(self, user_id: str) -> Optional[UserStats]:
        return self.db.query(UserStats).filter(UserStats.user_id == user_id).first()

    def get_stats(self, user_id: str) -> UserStatsDto:
        """获取用户统计（严格 get，不做隐式 create）。

        约束：
        - create_user 已经负责在同一事务里创建 user_stats（0/0）。
        - 因此这里查不到 stats 属于“数据不一致”，应显式暴露出来，便于定位/修复。
        """
        stats = self._get_stats_orm(user_id)
        if stats is None:
            raise RuntimeError(
                f"user_stats missing for user_id={user_id}; "
                f"this violates aggregate invariant (users/user_stats should be created together). "
                f"Please run a backfill/migration to repair historical data."
            )
        return UserStatsDto.model_validate(stats)

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> UserStatsDto:
        """增量更新统计（严格模式：不负责补建记录）。

        设计说明：
        - 统计记录应该由 create_user 统一初始化。
        - 这里如果查不到 stats，说明数据不一致，应该显式暴露，而不是在 update 时悄悄创建。
        """

        # 如果没有增量，直接返回当前统计（不创建）。
        if following_step == 0 and followers_step == 0:
            return self.get_stats(user_id)

        stats = self._get_stats_orm(user_id)
        if stats is None:
            raise RuntimeError(
                f"user_stats missing for user_id={user_id}; cannot update stats. "
                f"Please repair historical data first."
            )

        with transaction(self.db):
            if following_step != 0:
                stats.following_count = max(0, stats.following_count + following_step)
            if followers_step != 0:
                stats.followers_count = max(0, stats.followers_count + followers_step)

        self.db.refresh(stats)
        return UserStatsDto.model_validate(stats)

    def get_user_profile(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        """用户详情：UserOut + UserStatsDto。
        profile 是由 UserRepository 负责, 因为
            - 上层不关心 user_stats 数据表怎么查/是否存在。
            - repo 内部可以选择 join、lazy load、缓存等不同策略，而不影响业务层。
        """

        user = self._base_query().filter(User.uid == user_id).first()
        if not user:
            return None

        # 严格读取：统计信息应该存在，否则视为数据不一致。
        stats_dto = self.get_stats(user_id)

        return UserStatsWithUserOut(
            user_info=_to_user_out(user),
            user_stats=stats_dto,
        )
