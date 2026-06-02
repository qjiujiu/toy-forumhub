from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Dict, List


class EnergyDimension(Enum):
    """能量指向：Extraversion (外向) / Introversion (内向)"""
    E = "Extraversion"   # 外向
    I = "Introversion"   # 内向


class PerceptionDimension(Enum):
    """信息获取：Sensing (实感) / Intuition (直觉)"""
    S = "Sensing"    # 实感
    N = "Intuition"  # 直觉


class JudgmentDimension(Enum):
    """决策方式：Thinking (理性) / Feeling (情感)"""
    T = "Thinking"  # 理性
    F = "Feeling"   # 情感


class LifestyleDimension(Enum):
    """生活态度：Judging (计划) / Perceiving (灵活)"""
    J = "Judging"     # 计划
    P = "Perceiving"  # 灵活


class MBTIDimension(Enum):
    """MBTI 四维分类标签"""
    ENERGY = "E/I"
    PERCEPTION = "S/N"
    JUDGMENT = "T/F"
    LIFESTYLE = "J/P"


class MBTIType(Enum):
    """16 种 MBTI 人格类型"""
    ISTJ = "ISTJ"
    ISFJ = "ISFJ"
    INFJ = "INFJ"
    INTJ = "INTJ"
    ISTP = "ISTP"
    ISFP = "ISFP"
    INFP = "INFP"
    INTP = "INTP"
    ESTP = "ESTP"
    ESFP = "ESFP"
    ENFP = "ENFP"
    ENTP = "ENTP"
    ESTJ = "ESTJ"
    ESFJ = "ESFJ"
    ENFJ = "ENFJ"
    ENTJ = "ENTJ"

    @property
    def energy(self) -> EnergyDimension:
        return EnergyDimension.E if "E" in self.value else EnergyDimension.I

    @property
    def perception(self) -> PerceptionDimension:
        return PerceptionDimension.N if "N" in self.value else PerceptionDimension.S

    @property
    def judgment(self) -> JudgmentDimension:
        return JudgmentDimension.F if "F" in self.value else JudgmentDimension.T

    @property
    def lifestyle(self) -> LifestyleDimension:
        return LifestyleDimension.J if "J" in self.value else LifestyleDimension.P

    def to_tuple(self) -> tuple:
        return (self.energy, self.perception, self.judgment, self.lifestyle)

    @property
    def chinese_name(self) -> str:
        return _MBTI_CHINESE_NAMES[self]

    @property
    def chinese_description(self) -> str:
        return _MBTI_CHINESE_DESC[self]


_MBTI_CHINESE_NAMES: Dict[MBTIType, str] = {
    MBTIType.ISTJ: "检查员",
    MBTIType.ISFJ: "守护者",
    MBTIType.INFJ: "提倡者",
    MBTIType.INTJ: "建筑师",
    MBTIType.ISTP: "鉴赏家",
    MBTIType.ISFP: "探险家",
    MBTIType.INFP: "调停者",
    MBTIType.INTP: "逻辑家",
    MBTIType.ESTP: "企业家",
    MBTIType.ESFP: "表演者",
    MBTIType.ENFP: "活动家",
    MBTIType.ENTP: "辩论家",
    MBTIType.ESTJ: "总经理",
    MBTIType.ESFJ: "执政官",
    MBTIType.ENFJ: "主人公",
    MBTIType.ENTJ: "指挥官",
}

_MBTI_CHINESE_DESC: Dict[MBTIType, str] = {
    MBTIType.ISTJ: "安静、严肃、可靠，注重事实和细节，有极强的责任感和执行力",
    MBTIType.ISFJ: "安静、友善、有责任心，维护传统，乐于助人，注重细节",
    MBTIType.INFJ: "有洞察力和创造力，坚持理想，对人有深层的理解力",
    MBTIType.INTJ: "独立思考者，有战略眼光，追求效率和系统性，高标准严要求",
    MBTIType.ISTP: "灵活、冷静的观察者，擅长分析事物原理，动手能力强",
    MBTIType.ISFP: "安静、敏感、友善，有自己的审美和价值体系，热爱自然与艺术",
    MBTIType.INFP: "理想主义者，忠于自己的价值观，有强烈的创造力和同理心",
    MBTIType.INTP: "创新思考者，对理论问题充满好奇，喜欢逻辑分析",
    MBTIType.ESTP: "精力充沛、善于社交，行动派，喜欢影响和说服他人",
    MBTIType.ESFP: "热情开朗、善于社交，享受生活，喜欢成为焦点",
    MBTIType.ENFP: "充满热情和创造力，善于发现可能性，喜欢激励他人",
    MBTIType.ENTP: "思维敏捷、善于辩论，喜欢挑战常规，追求创新",
    MBTIType.ESTJ: "果断、有条理，天生的领导者，注重效率和秩序",
    MBTIType.ESFJ: "热心、健谈、善于合作，注重和谐，有强烈的责任感",
    MBTIType.ENFJ: "有魅力和感召力，善于理解和激励他人，天生的领导者",
    MBTIType.ENTJ: "果断、目标明确，擅长战略规划和执行，天生的指挥官",
}


@dataclass
class MBTIDistribution:
    """MBTI 在真实人口中的分布比例（美国人口统计数据）"""
    data: Dict[MBTIType, float]

    def sample_weight(self, mbti: MBTIType) -> float:
        return self.data.get(mbti, 0.0)

    def normalized_weights(self) -> Dict[MBTIType, float]:
        total = sum(self.data.values())
        return {k: v / total for k, v in self.data.items()}

    @property
    def ordered_by_weight(self) -> List[MBTIType]:
        return sorted(self.data.keys(), key=lambda t: self.data[t], reverse=True)


# 真实世界 MBTI 分布比例（基于美国人口统计数据）
REAL_WORLD_DISTRIBUTION: Dict[MBTIType, float] = {
    MBTIType.ISTJ: 13.8,
    MBTIType.ISFJ: 13.8,
    MBTIType.INFJ: 1.5,
    MBTIType.INTJ: 2.1,
    MBTIType.ISTP: 5.4,
    MBTIType.ISFP: 8.8,
    MBTIType.INFP: 4.4,
    MBTIType.INTP: 3.3,
    MBTIType.ESTP: 4.3,
    MBTIType.ESFP: 8.5,
    MBTIType.ENFP: 8.1,
    MBTIType.ENTP: 3.2,
    MBTIType.ESTJ: 8.7,
    MBTIType.ESFJ: 12.3,
    MBTIType.ENFJ: 2.5,
    MBTIType.ENTJ: 1.8,
}

DEFAULT_DISTRIBUTION = MBTIDistribution(data=REAL_WORLD_DISTRIBUTION)
