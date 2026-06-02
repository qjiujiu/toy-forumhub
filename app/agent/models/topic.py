from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum
from datetime import datetime


class TopicCategory(IntEnum):
    """选题分类"""
    TECHNOLOGY = 0       # 科技
    SOCIETY = 1          # 社会
    POLITICS = 2         # 政治
    ECONOMY = 3          # 经济
    CULTURE = 4          # 文化
    ENTERTAINMENT = 5    # 娱乐
    SPORTS = 6           # 体育
    LIFESTYLE = 7        # 生活方式
    EDUCATION = 8        # 教育
    HEALTH = 9           # 健康
    ENVIRONMENT = 10     # 环境
    OTHER = 99           # 其他


class TopicStatus(IntEnum):
    DRAFT = 0        # 草稿
    PUBLISHED = 1    # 已发布（Agent 可执行）
    CLOSED = 2       # 已关闭


@dataclass
class Topic:
    """
    选题模型。
    管理员定义的一个模拟话题，Agent 将围绕该话题生成内容。
    """
    topic_id: str                       # 选题唯一标识
    title: str                          # 选题标题
    description: str                    # 选题描述/背景说明
    category: TopicCategory             # 选题分类

    # --- 模拟参数 ---
    agent_count: int = 10               # 参与此话题的 Agent 数量
    post_count: int = 5                 # 预期发帖数量
    comment_depth: int = 2              # 评论深度（楼中楼层数）
    duration_hours: int = 48            # 模拟持续时间（小时）

    # --- 时间配置 ---
    start_time: Optional[datetime] = None       # 模拟开始时间
    end_time: Optional[datetime] = None         # 模拟结束时间
    created_at: datetime = field(default_factory=datetime.now)

    # --- 状态 ---
    status: TopicStatus = TopicStatus.DRAFT

    # --- 可选的附加信息 ---
    tags: list[str] = field(default_factory=list)       # 标签
    reference_links: list[str] = field(default_factory=list)  # 参考链接
    hot_keywords: list[str] = field(default_factory=list)     # 热门关键词
