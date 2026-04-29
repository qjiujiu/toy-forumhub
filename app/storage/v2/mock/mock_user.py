import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from app.schemas.v2.user import (
    UserCreate, UserOut, UserInfoDto, UserTimeDto, BatchUsersOut, UserUpdateDto,
)
from app.schemas.v2.user_stats import UserStatsDto, UserStatsWithUserOut
from app.models.v2.user import UserRole, UserStatus


class MockUserRepository:
    def __init__(self):
        self.users: Dict[str, UserOut] = {}
        self.passwords: Dict[str, str] = {}

        # user_stats 在真实系统里是一张独立的数据表。
        # 但是“数据访问层”希望屏蔽分表细节，因此这里把它作为 MockUserRepository 的内部存储。
        #
        # 知识点：Mock 设计目标
        # - Mock 并非了 100% 模拟数据库行为
        # - Mock 目标是让上层（service/api）在不依赖真实 DB 的情况下验证业务逻辑
        # - 因此 mock repo 边界应该和真实 repo 边界一致（对外只暴露一个聚合仓储）
        self._stats: Dict[str, UserStatsDto] = {}

    def get_password(self, uid: str) -> Optional[str]:
        return self.passwords.get(uid)

    def _base_query(self):
        return [u for u in self.users.values() if not u.user_data.deleted_at and u.user_info.status == UserStatus.NORMAL]

    def find_user(self, uid: Optional[str] = None, phone: Optional[str] = None) -> Optional[UserOut]:
        if uid:
            user = self.users.get(uid)
            if user and not user.user_data.deleted_at and user.user_info.status == UserStatus.NORMAL:
                return user
            return None
        elif phone:
            for u in self._base_query():
                if u.user_info.phone == phone:
                    return u
            return None
        return None

    def list_users(
        self,
        username: Optional[str] = None,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchUsersOut:
        matched = self._base_query()
        if username:
            matched = [u for u in matched if u.user_info.username == username]
        matched.sort(key=lambda x: x.user_data.created_at, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchUsersOut(total=len(matched), count=len(matched[start:end]), users=matched[start:end])

    def create_user(self, user_data: UserCreate) -> UserOut:
        uid = str(uuid.uuid4())
        now = datetime.now(timezone(timedelta(hours=8)))
        new_user = UserOut(
            uid=uid,
            user_info=UserInfoDto(
                username=user_data.username,
                phone=user_data.phone,
                role=UserRole.NORMAL_USER,
                status=UserStatus.NORMAL,
            ),
            user_data=UserTimeDto(
                created_at=now,
                updated_at=now,
            ),
        )
        self.users[uid] = new_user
        self.passwords[uid] = user_data.password

        # 创建用户时初始化统计信息（聚合内一致性）。
        # 这里直接写入默认值，而不是通过 get_or_create 做兜底，避免“读路径带写入”的误解。
        self._stats[uid] = UserStatsDto(following_count=0, followers_count=0)
        return new_user

    def update_user(self, uid: str, update_dto: UserUpdateDto) -> Optional[UserOut]:
        user = self.users.get(uid)
        if not user or user.user_data.deleted_at or user.user_info.status != UserStatus.NORMAL:
            return None

        now = datetime.now(timezone(timedelta(hours=8)))

        if update_dto.user_info is not None:
            ui = update_dto.user_info
            if ui.username is not None:
                user.user_info.username = ui.username
            if ui.phone is not None:
                user.user_info.phone = ui.phone
            if ui.email is not None:
                user.user_info.email = ui.email
            if ui.avatar_url is not None:
                user.user_info.avatar_url = ui.avatar_url
            if ui.bio is not None:
                user.user_info.bio = ui.bio
            if ui.role is not None:
                user.user_info.role = ui.role
            if ui.status is not None:
                user.user_info.status = ui.status

        if update_dto.user_data is not None:
            ud = update_dto.user_data
            if ud.last_login_at is not None:
                user.user_data.last_login_at = ud.last_login_at
            if ud.created_at is not None:
                user.user_data.created_at = ud.created_at
            if ud.updated_at is not None:
                user.user_data.updated_at = ud.updated_at
            if ud.deleted_at is not None:
                user.user_data.deleted_at = ud.deleted_at

        if update_dto.password is not None:
            self.passwords[uid] = update_dto.password

        user.user_data.updated_at = now
        return user

    def delete_user(self, uid: str) -> bool:
        if uid in self.users:
            del self.users[uid]
            if uid in self.passwords:
                del self.passwords[uid]

            # 真实数据库中 user_stats 可能配置了外键与级联删除。
            # 这里用显式删除模拟“硬删除用户后统计记录也不应残留”。
            self._stats.pop(uid, None)
            return True
        return False

    # ===================== 聚合能力：user_stats（mock 版） =====================

    def get_stats(self, user_id: str) -> UserStatsDto:
        stats = self._stats.get(user_id)
        if stats is None:
            raise RuntimeError(
                f"user_stats missing for user_id={user_id}; "
                f"this violates aggregate invariant (users/user_stats should be created together)."
            )
        return stats

    def update_stats(self, user_id: str, following_step: int = 0, followers_step: int = 0) -> UserStatsDto:
        if following_step == 0 and followers_step == 0:
            return self.get_stats(user_id)

        stat = self._stats.get(user_id)
        if stat is None:
            raise RuntimeError(f"user_stats missing for user_id={user_id}; cannot update stats")

        if following_step != 0:
            stat.following_count = max(0, stat.following_count + following_step)
        if followers_step != 0:
            stat.followers_count = max(0, stat.followers_count + followers_step)
        return stat

    def get_user_profile(self, user_id: str) -> Optional[UserStatsWithUserOut]:
        user = self.find_user(uid=user_id)
        if not user:
            return None
        stats = self.get_stats(user_id)
        return UserStatsWithUserOut(user_info=user, user_stats=stats)
