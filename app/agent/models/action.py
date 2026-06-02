from dataclasses import dataclass, field
from typing import Optional, Any
from enum import IntEnum
from datetime import datetime


class ActionType(IntEnum):
    """Agent 可执行的动作类型"""
    CREATE_POST = 0      # 发帖
    CREATE_COMMENT = 1   # 评论
    LIKE_POST = 2        # 点赞帖子
    LIKE_COMMENT = 3     # 点赞评论
    FOLLOW_USER = 4      # 关注用户
    REPLY_COMMENT = 5    # 回复评论


class ActionResult(IntEnum):
    PENDING = 0      # 待执行
    SUCCESS = 1      # 成功
    FAILED = 2       # 失败
    SKIPPED = 3      # 跳过（如已点赞过）


@dataclass
class AgentAction:
    """
    Agent 行为记录。
    记录每个 Agent 计划执行或已执行的动作。
    """
    action_id: str                      # 动作唯一标识
    agent_id: str                       # 执行此动作的 Agent ID
    action_type: ActionType             # 动作类型
    topic_id: str                       # 关联的选题 ID

    # --- 目标对象 ---
    target_id: Optional[str] = None     # 操作对象 ID（帖子 pid / 评论 cid / 用户 uid）
    target_author_id: Optional[str] = None  # 目标作者 ID（用于评论/点赞时确定上下文）

    # --- 生成的内容 ---
    content: Optional[str] = None       # LLM 生成的内容文本（发帖/评论时使用）
    title: Optional[str] = None         # 帖子标题（发帖时使用）

    # --- 执行状态 ---
    result: ActionResult = ActionResult.PENDING
    error_message: Optional[str] = None  # 失败原因
    executed_at: Optional[datetime] = None  # 执行时间

    # --- 元信息 ---
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None  # 计划执行时间
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外信息（如 LLM 花费的 token 数）
