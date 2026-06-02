from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum
from datetime import datetime

from app.agent.models.mbti import MBTIType


class AgentStatus(IntEnum):
    INACTIVE = 0   # 未激活
    ACTIVE = 1     # 活跃
    PAUSED = 2     # 暂停


@dataclass
class AgentProfile:
    """
    Agent 智能体档案。
    每个 Agent 对应论坛中的一个虚拟用户，拥有人格、背景、行为参数等定义。
    """
    agent_id: str                       # Agent 唯一标识
    mbti_type: MBTIType                 # MBTI 人格类型

    # --- 基础信息 ---
    username: str                       # 论坛用户名（对应 User 表）
    user_uid: str                       # 论坛用户 UID（对应 User 表）
    nickname: str = ""                  # 昵称/显示名
    age: int = 30                       # 年龄
    gender: str = "unknown"             # 性别

    # --- 背景设定 ---
    occupation: str = ""                # 职业
    background_story: str = ""          # 背景故事/人设
    interests: list[str] = field(default_factory=list)   # 兴趣标签

    # --- 行为特征权重（0.0 ~ 1.0，影响行为调度器的采样概率）---
    post_frequency: float = 0.5         # 发帖活跃度
    comment_frequency: float = 0.5      # 评论活跃度
    like_probability: float = 0.5       # 点赞概率
    follow_probability: float = 0.3     # 关注概率

    # --- 状态 ---
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def is_active(self) -> bool:
        return self.status == AgentStatus.ACTIVE
