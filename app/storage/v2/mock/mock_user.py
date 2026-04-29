import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from app.core.time import now_utc8
from app.schemas.v2.user import (
    BatchUsersOut,
    UserInfoDto,
    UserOut,
    UserTimeDto,
)
from app.schemas.v2.user_req import UserPatch, UserInfoPatch, UserAdminPatch, UserPasswordPatch
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
        # - Mock 并非是为了 100% 模拟数据库行为
        # - Mock 目标是让上层（service/api）在不依赖真实 DB 的情况下验证业务逻辑
        # - 因此 mock repo 边界应该和真实 repo 边界一致（对外只暴露一个聚合仓储）
        self._stats: Dict[str, UserStatsDto] = {}

        # 默认预加载 scripts/mock_data：模拟“数据库本来就有的数据”
        self._preload_seed_data()

    @classmethod
    def empty(cls) -> "MockUserRepository":
        repo = cls()
        repo.clear_all()
        return repo

    def clear_all(self) -> None:
        self.users.clear()
        self.passwords.clear()
        self._stats.clear()

    def _seed_dir(self) -> Path:
        # repo_root/scripts/mock_data
        # 当前文件：app/storage/v2/mock/mock_user.py
        repo_root = Path(__file__).resolve().parents[4]
        return repo_root / "scripts" / "mock_data"

    def _load_json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _preload_seed_data(self) -> None:
        seed_dir = self._seed_dir()
        users = self._load_json(seed_dir / "users.json")
        stats = self._load_json(seed_dir / "user_stats.json")

        stats_by_uid = {row["user_id"]: row for row in stats}

        # 默认加载全部 seed users
        for row in users:
            uid = row["uid"]

            # scripts/mock_data 里面没提供 created_at/updated_at，这里用 now_utc8 填充。
            now = now_utc8()

            # 利用 UserOut 扁平输入适配（user_dto.py 的 model_validator）
            user_out = UserOut.model_validate(
                {
                    "uid": uid,
                    **row,
                    "created_at": now,
                    "updated_at": now,
                    "deleted_at": None,
                }
            )

            self.users[uid] = user_out
            self.passwords[uid] = row["password"]
            self._stats[uid] = UserStatsDto.model_validate(stats_by_uid[uid])

    def get_password(self, uid: str) -> Optional[str]:
        return self.passwords.get(uid)

    def _base_query(self):
        return [
            u
            for u in self.users.values()
            if (not u.user_data.deleted_at and u.user_info.status == UserStatus.NORMAL)
        ]

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
        page_users = matched[start:end]
        return BatchUsersOut(
            total=len(matched),
            count=len(page_users),
            users=page_users,
        )

    def create_user(self, username: str, phone: str, hashed_password: str) -> UserOut:
        uid = str(uuid.uuid4())
        now = datetime.now(timezone(timedelta(hours=8)))
        new_user = UserOut(
            uid=uid,
            user_info=UserInfoDto(
                username=username,
                phone=phone,
                role=UserRole.NORMAL_USER,
                status=UserStatus.NORMAL,
            ),
            user_data=UserTimeDto(
                created_at=now,
                updated_at=now,
            ),
        )
        self.users[uid] = new_user
        self.passwords[uid] = hashed_password

        # 创建用户时初始化统计信息（聚合内一致性）。
        # 这里直接写入默认值，而不是通过 get_or_create 做兜底，避免“读路径带写入”的误解。
        self._stats[uid] = UserStatsDto(following_count=0, followers_count=0)
        return new_user

    # 通用更新入口（CRUD + 通用 update）
    def update_user(self, uid: str, patch: UserPatch) -> Optional[UserOut]:
        user = self.users.get(uid)
        if not user or user.user_data.deleted_at:
            return None

        # 现在 update_data 里的枚举会被 model_dump 转成 int（UserAdminPatch.use_enum_values=True）
        update_data = patch.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "password":
                # mock 仓库把 password 单独存到 passwords 字典里
                self.passwords[uid] = value
                continue

            if field == "deleted_at":
                user.user_data.deleted_at = value
                continue

            if field == "role":
                user.user_info.role = UserRole(value)
                continue

            if field == "status":
                user.user_info.status = UserStatus(value)
                continue

            if hasattr(user.user_info, field):
                setattr(user.user_info, field, value)
                continue

            raise TypeError(f"unsupported user patch field: {field!r}")

        user.user_data.updated_at = datetime.now(timezone(timedelta(hours=8)))
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
