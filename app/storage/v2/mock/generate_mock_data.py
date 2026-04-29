"""生成 v2 mock JSON 数据。

目标：为后续测试准备“接近真实数据库”的种子数据（list[dict] JSON），并且：
- id 带有人类可读前缀，便于写断言与排查（例如 usr_alice_... / post_clean_arch_...）
- 密码使用项目内的 hash_password 生成 hash（而不是随便写字符串）

用法：
    python app/storage/v2/mock/generate_mock_data.py
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.core.security import hash_password


BASE_DIR = Path(__file__).resolve().parent
TZ_UTC8 = timezone(timedelta(hours=8))


def _ts(year: int, month: int, day: int, hour: int, minute: int, second: int = 0) -> str:
    return datetime(year, month, day, hour, minute, second, tzinfo=TZ_UTC8).isoformat()


def _make_id(prefix: str) -> str:
    # 保留 UUID 以保证全局唯一，同时用 prefix 让断言/排查更直观。
    return f"{prefix}_{uuid.uuid4()}"


@dataclass(frozen=True)
class Ids:
    alice_uid: str
    bob_uid: str
    admin_uid: str
    p_clean_arch: str
    p_cqrs_draft: str
    p_private_bug: str
    p_deleted_refactor: str


def build_ids() -> Ids:
    return Ids(
        alice_uid=_make_id("usr_alice"),
        bob_uid=_make_id("usr_bob"),
        admin_uid=_make_id("usr_admin"),
        p_clean_arch=_make_id("post_clean_arch"),
        p_cqrs_draft=_make_id("post_cqrs_draft"),
        p_private_bug=_make_id("post_private_bug"),
        p_deleted_refactor=_make_id("post_deleted_refactor"),
    )


def build_users(ids: Ids) -> List[Dict[str, Any]]:
    return [
        {
            "_id": 1,
            "uid": ids.alice_uid,
            "username": "alice",
            "role": 0,
            "status": 0,
            "phone": "13800000001",
            "password": hash_password("alice_pw_2026"),
            "avatar_url": "https://example.com/avatars/alice.png",
            "email": "alice@example.com",
            "bio": "后端开发，喜欢写测试与重构。",
            "last_login_at": _ts(2026, 4, 28, 9, 10),
            "created_at": _ts(2026, 4, 1, 10, 0),
            "updated_at": _ts(2026, 4, 28, 9, 10),
            "deleted_at": None,
        },
        {
            "_id": 2,
            "uid": ids.bob_uid,
            "username": "bob",
            "role": 0,
            "status": 0,
            "phone": "13800000002",
            "password": hash_password("bob_pw_2026"),
            "avatar_url": "https://example.com/avatars/bob.png",
            "email": "bob@example.com",
            "bio": "产品爱好者，爱写长帖。",
            "last_login_at": _ts(2026, 4, 27, 21, 30),
            "created_at": _ts(2026, 4, 2, 11, 20),
            "updated_at": _ts(2026, 4, 27, 21, 30),
            "deleted_at": None,
        },
        {
            "_id": 3,
            "uid": ids.admin_uid,
            "username": "admin",
            "role": 2,
            "status": 0,
            "phone": "13800000003",
            "password": hash_password("admin_pw_2026"),
            "avatar_url": "https://example.com/avatars/admin.png",
            "email": "admin@example.com",
            "bio": "管理员账号，用于审核与封禁操作。",
            "last_login_at": _ts(2026, 4, 29, 8, 0),
            "created_at": _ts(2026, 3, 20, 9, 0),
            "updated_at": _ts(2026, 4, 29, 8, 0),
            "deleted_at": None,
        },
    ]


def build_user_stats(ids: Ids) -> List[Dict[str, Any]]:
    return [
        {
            "_id": 1,
            "user_id": ids.alice_uid,
            "following_count": 12,
            "followers_count": 34,
            "updated_at": _ts(2026, 4, 28, 9, 10),
        },
        {
            "_id": 2,
            "user_id": ids.bob_uid,
            "following_count": 5,
            "followers_count": 18,
            "updated_at": _ts(2026, 4, 27, 21, 30),
        },
        {
            "_id": 3,
            "user_id": ids.admin_uid,
            "following_count": 0,
            "followers_count": 0,
            "updated_at": _ts(2026, 4, 29, 8, 0),
        },
    ]


def build_posts(ids: Ids) -> List[Dict[str, Any]]:
    return [
        {
            "_id": 1,
            "pid": ids.p_clean_arch,
            "author_id": ids.alice_uid,
            "visibility": 0,
            "publish_status": 1,
            "deleted_at": None,
        },
        {
            "_id": 2,
            "pid": ids.p_cqrs_draft,
            "author_id": ids.bob_uid,
            "visibility": 0,
            "publish_status": 0,
            "deleted_at": None,
        },
        {
            "_id": 3,
            "pid": ids.p_private_bug,
            "author_id": ids.bob_uid,
            "visibility": 1,
            "publish_status": 2,
            "deleted_at": None,
        },
        {
            "_id": 4,
            "pid": ids.p_deleted_refactor,
            "author_id": ids.alice_uid,
            "visibility": 0,
            "publish_status": 1,
            "deleted_at": _ts(2026, 4, 15, 12, 0),
        },
    ]


def build_post_contents(ids: Ids) -> List[Dict[str, Any]]:
    return [
        {
            "_id": 1,
            "pcid": _make_id("pc_clean_arch"),
            "post_id": ids.p_clean_arch,
            "title": "为什么 service 层不应该依赖 req schema？",
            "content": "重构 create_user：service 接收 primitives，API 层负责 schema 校验与解包。",
            "created_at": _ts(2026, 4, 10, 9, 0),
            "updated_at": _ts(2026, 4, 28, 9, 0),
        },
        {
            "_id": 2,
            "pcid": _make_id("pc_cqrs_draft"),
            "post_id": ids.p_cqrs_draft,
            "title": "草稿：我们要不要引入 CQRS？",
            "content": "列出优缺点：读写分离、复杂度提升、团队学习成本...",
            "created_at": _ts(2026, 4, 20, 14, 20),
            "updated_at": _ts(2026, 4, 20, 14, 20),
        },
        {
            "_id": 3,
            "pcid": _make_id("pc_private_bug"),
            "post_id": ids.p_private_bug,
            "title": "仅作者可见：排查线上 bug 的过程记录",
            "content": "包含敏感信息，仅作者可见。记录复现步骤与临时修复方案。",
            "created_at": _ts(2026, 4, 18, 22, 10),
            "updated_at": _ts(2026, 4, 19, 8, 30),
        },
        {
            "_id": 4,
            "pcid": _make_id("pc_deleted_refactor"),
            "post_id": ids.p_deleted_refactor,
            "title": "已删除：一次失败的重构尝试",
            "content": "踩坑记录：过早抽象导致接口泛化，阅读成本上升。",
            "created_at": _ts(2026, 4, 12, 11, 0),
            "updated_at": _ts(2026, 4, 15, 12, 0),
        },
    ]


def build_post_stats(ids: Ids) -> List[Dict[str, Any]]:
    return [
        {
            "_id": 1,
            "psid": _make_id("ps_clean_arch"),
            "post_id": ids.p_clean_arch,
            "like_count": 21,
            "comment_count": 6,
            "created_at": _ts(2026, 4, 10, 9, 0),
        },
        {
            "_id": 2,
            "psid": _make_id("ps_cqrs_draft"),
            "post_id": ids.p_cqrs_draft,
            "like_count": 0,
            "comment_count": 0,
            "created_at": _ts(2026, 4, 20, 14, 20),
        },
        {
            "_id": 3,
            "psid": _make_id("ps_private_bug"),
            "post_id": ids.p_private_bug,
            "like_count": 3,
            "comment_count": 1,
            "created_at": _ts(2026, 4, 18, 22, 10),
        },
        {
            "_id": 4,
            "psid": _make_id("ps_deleted_refactor"),
            "post_id": ids.p_deleted_refactor,
            "like_count": 8,
            "comment_count": 2,
            "created_at": _ts(2026, 4, 12, 11, 0),
        },
    ]


def _write_json(path: Path, data: List[Dict[str, Any]]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ids = build_ids()

    _write_json(BASE_DIR / "users.json", build_users(ids))
    _write_json(BASE_DIR / "user_stats.json", build_user_stats(ids))
    _write_json(BASE_DIR / "posts.json", build_posts(ids))
    _write_json(BASE_DIR / "post_contents.json", build_post_contents(ids))
    _write_json(BASE_DIR / "post_stats.json", build_post_stats(ids))

    print("ok: generated mock json under", str(BASE_DIR))


if __name__ == "__main__":
    main()

