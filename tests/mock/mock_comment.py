"""
聚合仓储风格的 MockCommentRepository。

物理上 comments / comment_contents 是两张独立表，
本 Mock 用一个对象内部维护两份字典，屏蔽多表细节，
对外以"一个评论聚合"的形式提供读写能力，对齐 ICommentRepository 协议。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from app.schemas.v2.comment import (
    CommentCreate,
    CommentOnlyCreate,
    CommentOut,
    BatchCommentsOut,
    StatusUpdate,
    CommentQuery,
    CommentUpdate,
)
from app.schemas.v2.comment_content import CommentContentOut


def _now():
    return datetime.now(timezone(timedelta(hours=8)))


class MockCommentRepository:
    """Mock 聚合仓储：内部维护 comments/contents 两份字典，对外以聚合方式操作。"""

    def __init__(self, post_repo=None, user_repo=None):
        self.comments: Dict[str, dict] = {}
        self.contents: Dict[str, CommentContentOut] = {}
        self._post_repo = post_repo
        self._user_repo = user_repo

    @classmethod
    def empty(cls, post_repo=None, user_repo=None):
        return cls(post_repo=post_repo, user_repo=user_repo)

    # ========== 增 ==========

    def create(self, data: CommentOnlyCreate) -> str:
        cid = str(uuid.uuid4())
        self.comments[cid] = {
            "cid": cid,
            "post_id": data.post_id,
            "author_id": data.author_id,
            "parent_id": data.parent_id,
            "root_id": data.root_id,
            "like_count": 0,
            "comment_count": 0,
            "status": 0,
            "review_status": 0,
            "deleted": False,
        }
        return cid

    def create_comment(self, data: CommentCreate) -> CommentOut:
        root_id = data.root_id or ""
        cid = self.create(CommentOnlyCreate(
            post_id=data.post_id,
            author_id=data.author_id,
            parent_id=data.parent_id,
            root_id=root_id,
        ))
        # 首层评论 root_id 设为自身
        if data.root_id is None:
            self.comments[cid]["root_id"] = cid

        now = _now()
        content = CommentContentOut(
            ccid=str(uuid.uuid4()),
            comment_id=cid,
            content=data.content,
            created_at=now,
            updated_at=now,
        )
        self.contents[cid] = content
        return self._build_out(cid)

    # ========== 查 ==========

    def _build_out(self, cid: str) -> Optional[CommentOut]:
        c = self.comments.get(cid)
        if not c or c.get("deleted"):
            return None
        content = self.contents.get(cid)
        if not content:
            return None
        return CommentOut(
            cid=c["cid"],
            post_id=c["post_id"],
            author_id=c["author_id"],
            comment_content=content,
            parent_id=c.get("parent_id"),
            root_id=c.get("root_id"),
            comment_count=c.get("comment_count", 0),
            like_count=c.get("like_count", 0),
            status=c.get("status", 0),
            review_status=c.get("review_status", 0),
        )

    def get_by_cid(self, cid: str) -> Optional[CommentOut]:
        return self._build_out(cid)

    def get_comments(self, query: CommentQuery, page: int = 0, page_size: int = 20) -> BatchCommentsOut:
        matched = []
        for c in self.comments.values():
            if c.get("deleted"):
                continue
            if query.root_id is not None and c.get("root_id") != query.root_id:
                continue
            if query.parent_id is not None and c.get("parent_id") != query.parent_id:
                continue
            if query.author_id is not None and c.get("author_id") != query.author_id:
                continue
            if query.post_id is not None and c.get("post_id") != query.post_id:
                continue
            out = self._build_out(c["cid"])
            if out:
                matched.append(out)

        matched.sort(key=lambda x: x.cid, reverse=True)
        start = page * page_size
        end = start + page_size
        return BatchCommentsOut(total=len(matched), count=len(matched[start:end]), items=matched[start:end])

    # ========== 改 ==========

    def update(self, cid: str, data: StatusUpdate) -> bool:
        c = self.comments.get(cid)
        if not c or c.get("deleted"):
            return False
        if data.status is not None:
            c["status"] = data.status.value if hasattr(data.status, 'value') else data.status
        if data.review_status is not None:
            c["review_status"] = data.review_status.value if hasattr(data.review_status, 'value') else data.review_status
        return True

    def update_counters(self, cid: str, data: CommentUpdate) -> bool:
        c = self.comments.get(cid)
        if not c or c.get("deleted"):
            return False
        if data.like_count_delta:
            c["like_count"] = max(0, c["like_count"] + data.like_count_delta)
        if data.comment_count_delta:
            c["comment_count"] = max(0, c["comment_count"] + data.comment_count_delta)
        return True

    # ========== 删 ==========

    def hard_delete(self, cid: str) -> bool:
        if cid in self.comments:
            del self.comments[cid]
            self.contents.pop(cid, None)
            return True
        return False

    def soft_delete(self, cid: str) -> bool:
        c = self.comments.get(cid)
        if not c or c.get("deleted"):
            return False
        c["deleted"] = True
        return True
