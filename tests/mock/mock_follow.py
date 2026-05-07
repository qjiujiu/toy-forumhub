"""
聚合仓储风格的 MockFollowRepository。

对齐 IFollowRepository 协议。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from app.schemas.v2.follow import (
    FollowCreate,
    FollowCancel,
    FollowDto,
    FollowOut,
    BatchFollowsOut,
)
from app.schemas.user import UserOut, UserStatus
from app.models.user import UserRole

from app.core.exceptions import AlreadyFollowingError, NotFollowingError


def _now():
    return datetime.now(timezone(timedelta(hours=8)))


def _make_user_out(uid: str, username: str = "") -> UserOut:
    return UserOut(
        uid=uid,
        username=username or f"user_{uid[:8]}",
        role=UserRole.NORMAL_USER,
        status=UserStatus.NORMAL.value,
    )


class MockFollowRepository:
    """Mock 关注仓储：内部维护字典，屏蔽数据库细节。"""

    def __init__(self, user_repo=None):
        self.follows: Dict[str, dict] = {}
        self._user_repo = user_repo

    @classmethod
    def empty(cls, user_repo=None):
        return cls(user_repo=user_repo)

    def _lookup_user(self, uid: str) -> UserOut:
        """用 user_repo 查找用户，将 v2 UserOut 转为旧版 UserOut 扁平结构。"""
        if self._user_repo:
            v2_user = self._user_repo.find_user(uid=uid)
            if v2_user:
                return UserOut(
                    uid=v2_user.uid,
                    username=v2_user.user_info.username or "",
                    role=v2_user.user_info.role or UserRole.NORMAL_USER,
                    status=v2_user.user_info.status or UserStatus.NORMAL.value,
                )
        return _make_user_out(uid=uid)

    # ==================== C ====================

    def follow(self, data: FollowCreate) -> bool:
        for l in self.follows.values():
            if l["user_id"] == data.user_id and l["followed_user_id"] == data.followed_user_id:
                if l.get("deleted_at") is None:
                    raise AlreadyFollowingError(data.user_id, data.followed_user_id)
                l["deleted_at"] = None
                return True

        key = str(uuid.uuid4())
        self.follows[key] = {
            "key": key,
            "user_id": data.user_id,
            "followed_user_id": data.followed_user_id,
            "deleted_at": None,
        }
        return True

    # ==================== D ====================

    def unfollow(self, data: FollowCancel) -> bool:
        for l in self.follows.values():
            if l["user_id"] == data.user_id and l["followed_user_id"] == data.followed_user_id:
                if l.get("deleted_at") is not None:
                    raise NotFollowingError(
                        data.user_id, data.followed_user_id,
                        message="already unfollowed",
                    )
                l["deleted_at"] = _now()
                return True

        raise NotFollowingError(data.user_id, data.followed_user_id)

    def hard_unfollow(self, data: FollowCancel) -> bool:
        for key, l in list(self.follows.items()):
            if l["user_id"] == data.user_id and l["followed_user_id"] == data.followed_user_id:
                del self.follows[key]
                return True

        raise NotFollowingError(data.user_id, data.followed_user_id)

    # ==================== R ====================

    def get_follows(
        self,
        query: FollowDto,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchFollowsOut:
        matched = []
        for l in self.follows.values():
            if l.get("deleted_at") is not None:
                continue
            if query.user_id is not None and l["user_id"] != query.user_id:
                continue
            if query.followed_user_id is not None and l["followed_user_id"] != query.followed_user_id:
                continue

            # 确定"对方"用户
            if query.followed_user_id is not None and query.user_id is None:
                target_uid = l["user_id"]
                source_uid = l["followed_user_id"]
            else:
                target_uid = l["followed_user_id"]
                source_uid = l["user_id"]

            target_user = self._lookup_user(target_uid)

            # 互关检测：target 是否也关注了 source
            is_mutual = any(
                x["user_id"] == target_uid
                and x["followed_user_id"] == source_uid
                and x.get("deleted_at") is None
                for x in self.follows.values()
            )

            matched.append(FollowOut(user=target_user, is_mutual=is_mutual))

        matched.sort(key=lambda x: x.user.uid, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchFollowsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])
