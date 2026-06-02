import uuid
import logging
from typing import Callable, Dict, List, Optional
from datetime import datetime

from app.agent.models.mbti import MBTIType
from app.agent.models.profile import AgentProfile, AgentStatus
from app.agent.personas.matrix import ALL_PERSONAS
from app.agent.personas.traits import ALL_TRAITS

logger = logging.getLogger(__name__)


# 生成密码和手机号的固定前缀（便于识别 Agent 账号）
_AGENT_PASSWORD_PREFIX = "Agent@"
_AGENT_PHONE_PREFIX = "1380000"


def _make_username(mbti_type: MBTIType, index: int) -> str:
    """生成论坛用户名：MBTI 类型 + 序号"""
    return f"{mbti_type.value}_{index:04d}"


def _make_nickname(mbti_type: MBTIType, index: int) -> str:
    """生成显示昵称：人格中文名 + 昵称后缀"""
    chinese_name = ALL_PERSONAS[mbti_type].chinese_name
    suffix_candidates = ["同学", "先生", "女士", "君", "酱", ""]
    suffix = suffix_candidates[index % len(suffix_candidates)]
    return f"{chinese_name}{index}{suffix}"


def _make_password(mbti_type: MBTIType, index: int) -> str:
    """生成账号密码"""
    return f"{_AGENT_PASSWORD_PREFIX}{mbti_type.value}{index}"


def _make_phone(mbti_type: MBTIType, index: int) -> str:
    """生成虚拟手机号"""
    seq = (hash(f"{mbti_type.value}_{index}") & 0xFFFF) % 10000
    return f"{_AGENT_PHONE_PREFIX}{seq:04d}"


def _make_background_story(mbti_type: MBTIType, age: int, occupation: str) -> str:
    """根据人格特征生成简短背景故事"""
    persona = ALL_PERSONAS[mbti_type]
    chinese_name = persona.chinese_name
    keywords = "、".join(persona.keywords[:3])
    return (
        f"一位{age}岁的{occupation}，{persona.communication_style}。"
        f"典型特征：{keywords}。"
        f"在论坛上喜欢{'、'.join(persona.keywords[3:5])}的讨论氛围。"
    )


class AgentGenerator:
    """
    Agent 批量生成器。

    从采样好的 MBTI 类型列表出发，为每个类型创建对应的论坛用户和 AgentProfile。
    创建真实用户的逻辑通过回调函数注入，保持与 UserSvc 的解耦。

    Usage:
        sampler = MBTISampler(seed=42)
        mbti_types = sampler.sample(100)

        generator = AgentGenerator(create_user_callback=user_service.create_user)
        agents = generator.generate_all(mbti_types)
    """

    def __init__(
        self,
        create_user_callback: Optional[Callable] = None,
    ):
        """
        Args:
            create_user_callback: 创建论坛用户的回调函数。
                签名: (username: str, password: str, phone: str) -> user_uid: str
                传入 None 时使用模拟模式（不真实创建用户，仅生成 Profile）。
        """
        self._create_user = create_user_callback
        self._registry: Dict[str, AgentProfile] = {}

    def generate_all(
        self,
        mbti_types: List[MBTIType],
        start_index: int = 1,
    ) -> List[AgentProfile]:
        """
        批量生成 Agent。

        Args:
            mbti_types: 采样好的 MBTI 类型列表
            start_index: 序号起始值

        Returns:
            AgentProfile 列表
        """
        profiles: List[AgentProfile] = []
        type_counters: Dict[str, int] = {}

        for mbti_type in mbti_types:
            key = mbti_type.value
            type_counters[key] = type_counters.get(key, 0) + 1
            idx = type_counters[key]

            profile = self._generate_one(mbti_type, idx + start_index - 1)
            profiles.append(profile)
            self._registry[profile.agent_id] = profile

        logger.info(
            f"[AgentGenerator] Generated {len(profiles)} agents "
            f"({len(set(mbti_types))} MBTI types)"
        )
        return profiles

    def _generate_one(self, mbti_type: MBTIType, index: int) -> AgentProfile:
        """生成单个 Agent"""
        traits = ALL_TRAITS[mbti_type]
        persona = ALL_PERSONAS[mbti_type]

        username = _make_username(mbti_type, index)
        password = _make_password(mbti_type, index)
        phone = _make_phone(mbti_type, index)

        # 创建论坛真实用户
        user_uid = self._create_forum_user(username, password, phone)

        # 从人格特征中提取参数
        age_min, age_max = traits.typical_age_range
        age = (age_min + age_max) // 2
        occupation = traits.typical_occupations[index % len(traits.typical_occupations)]

        # 社交行为参数映射到 AgentProfile
        social = traits.social_params
        topic_weights = traits.topic_interest.weights
        top_interests = sorted(topic_weights, key=topic_weights.get, reverse=True)[:3]

        profile = AgentProfile(
            agent_id=str(uuid.uuid4()),
            mbti_type=mbti_type,
            username=username,
            user_uid=user_uid,
            nickname=_make_nickname(mbti_type, index),
            age=age,
            gender="male" if index % 2 == 0 else "female",
            occupation=occupation,
            background_story=_make_background_story(mbti_type, age, occupation),
            interests=[c.name.lower() for c in top_interests],
            post_frequency=round(1 - traits.writing_style.formality * 0.6, 2),
            comment_frequency=round(social.comment_ratio, 2),
            like_probability=round(social.like_ratio, 2),
            follow_probability=round(social.follow_ratio, 2),
            status=AgentStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return profile

    def _create_forum_user(self, username: str, password: str, phone: str) -> str:
        """调用回调创建论坛用户，失败时生成一个模拟 UID"""
        if self._create_user is not None:
            try:
                result = self._create_user(
                    username=username,
                    password=password,
                    phone=phone,
                )
                if isinstance(result, dict):
                    return result.get("uid", str(uuid.uuid4()))
                if isinstance(result, str):
                    return result
                return getattr(result, "uid", str(uuid.uuid4()))
            except Exception as e:
                logger.warning(
                    f"[AgentGenerator] Failed to create forum user '{username}': "
                    f"{e}. Using simulated UID."
                )
        return f"agent_{uuid.uuid4().hex[:12]}"

    def get_by_agent_id(self, agent_id: str) -> Optional[AgentProfile]:
        """按 agent_id 查找"""
        return self._registry.get(agent_id)

    def get_by_user_uid(self, user_uid: str) -> Optional[AgentProfile]:
        """按论坛 user_uid 查找"""
        for p in self._registry.values():
            if p.user_uid == user_uid:
                return p
        return None

    def list_active(self) -> List[AgentProfile]:
        """获取所有活跃 Agent"""
        return [p for p in self._registry.values() if p.is_active]

    @property
    def agent_count(self) -> int:
        return len(self._registry)

    @property
    def registry(self) -> Dict[str, AgentProfile]:
        return dict(self._registry)
