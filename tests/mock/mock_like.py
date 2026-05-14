"""
聚合仓储风格的 MockLikeRepository。

对齐 ILikeRepository 协议：
- create_or_restore: 创建新点赞 / 恢复已取消的点赞
- get_likes: 按字段动态过滤查询（LikeDto）
- cancel: 取消点赞（软删除）
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from app.schemas.v2.like import (
    LikeCreate,
    LikeCancel,
    LikeDto,
    LikeOut,
    BatchLikesOut,
)
from app.kit.exceptions import AlreadyLikedError, NotLikedError


def _now():
    return datetime.now(timezone(timedelta(hours=8)))


class MockLikeRepository:
    """Mock 点赞仓储：内部维护字典，屏蔽数据库细节。"""

    def __init__(self):
        self.likes: Dict[str, dict] = {}

    @classmethod
    def empty(cls):
        return cls()

    # ==================== C ====================

    def create_or_restore(self, data: LikeCreate) -> LikeOut:
        """
        创建新点赞，或恢复已取消的点赞。

        - 已存在且 deleted_at IS NULL → 抛 AlreadyLikedError
        - 已存在且 deleted_at IS NOT NULL → 重置 deleted_at=NULL, updated_at=now
        - 不存在 → 新建
        """
        # 查找已有记录
        target_val = data.target_type.value if hasattr(data.target_type, 'value') else data.target_type
        existing = None
        for l in self.likes.values():
            if (l["user_id"] == data.user_id
                    and l["target_type"] == target_val
                    and l["target_id"] == data.target_id):
                existing = l
                break

        now = _now()

        if existing:
            if existing.get("deleted_at") is None:
                raise AlreadyLikedError(data.user_id, data.target_type, data.target_id)
            # 恢复
            existing["deleted_at"] = None
            existing["updated_at"] = now
            return self._build_out(existing["lid"])

        # 全新创建
        lid = str(uuid.uuid4())
        self.likes[lid] = {
            "lid": lid,
            "user_id": data.user_id,
            "target_type": target_val,
            "target_id": data.target_id,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        return self._build_out(lid)

    # ==================== R ====================

    def get_likes(
        self,
        query: LikeDto,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchLikesOut:
        """
        按 query 中非 None 字段动态过滤，排除软删除。
        """
        matched = []
        for l in self.likes.values():
            if l.get("deleted_at") is not None:
                continue

            if query.user_id is not None and l["user_id"] != query.user_id:
                continue

            query_target = query.target_type
            if query_target is not None:
                qv = query_target.value if hasattr(query_target, 'value') else query_target
                if l["target_type"] != qv:
                    continue

            if query.target_id is not None and l["target_id"] != query.target_id:
                continue

            out = self._build_out(l["lid"])
            if out:
                matched.append(out)

        matched.sort(key=lambda x: x.created_at, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchLikesOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    # ==================== D ====================

    def cancel(self, data: LikeCancel) -> bool:
        """
        取消点赞（软删除）。
        - 不存在 → 抛 NotLikedError
        - 已取消过（deleted_at 非空）→ 抛 NotLikedError
        - 有效 → 设 deleted_at=now
        """
        target_val = data.target_type.value if hasattr(data.target_type, 'value') else data.target_type
        for l in self.likes.values():
            if (l["user_id"] == data.user_id
                    and l["target_type"] == target_val
                    and l["target_id"] == data.target_id):
                if l.get("deleted_at") is not None:
                    raise NotLikedError(
                        data.user_id, data.target_type, data.target_id,
                        message=f"user {data.user_id} has already cancelled like "
                                f"on target_type={data.target_type} target_id={data.target_id}",
                    )
                l["deleted_at"] = _now()
                return True

        raise NotLikedError(data.user_id, data.target_type, data.target_id)

    # ==================== 内部 ====================

    def _build_out(self, lid: str) -> Optional[LikeOut]:
        l = self.likes.get(lid)
        if not l or l.get("deleted_at") is not None:
            return None
        return LikeOut(
            lid=l["lid"],
            user_id=l["user_id"],
            target_type=l["target_type"],
            target_id=l["target_id"],
            created_at=l["created_at"],
            updated_at=l["updated_at"],
        )
