from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.agent.models.mbti import (
    MBTIType,
    EnergyDimension,
    PerceptionDimension,
    JudgmentDimension,
    LifestyleDimension,
)


@dataclass
class MBTIDimensionScore:
    """MBTI 各维度的得分/倾向强度（-100 ~ +100）"""
    energy: int      # 负值=E(外向), 正值=I(内向)
    perception: int  # 负值=S(实感), 正值=N(直觉)
    judgment: int    # 负值=T(理性), 正值=F(情感)
    lifestyle: int   # 负值=J(计划), 正值=P(灵活)


@dataclass
class CognitiveStack:
    """MBTI 认知功能栈（按使用频率排序）"""
    dominant: str     # 主导功能
    auxiliary: str    # 辅助功能
    tertiary: str     # 第三功能
    inferior: str     # 劣势功能


@dataclass
class MBTIPersona:
    """完整人格画像"""
    mbti_type: MBTIType
    chinese_name: str
    dimension_score: MBTIDimensionScore
    cognitive_stack: CognitiveStack
    keywords: List[str]          # 人格关键词
    strengths: List[str]         # 优势
    weaknesses: List[str]        # 劣势
    communication_style: str     # 沟通风格描述


# ──────────────────────────────────────────────
# 16 型人格认知功能栈
# 基于 Jung 心理学和 MBTI 官方理论
# ──────────────────────────────────────────────

_COGNITIVE_STACKS: Dict[MBTIType, CognitiveStack] = {
    # ---- SJ 护卫者类型（Si 主导）----
    MBTIType.ISTJ: CognitiveStack(dominant="Si", auxiliary="Te", tertiary="Fi", inferior="Ne"),
    MBTIType.ISFJ: CognitiveStack(dominant="Si", auxiliary="Fe", tertiary="Ti", inferior="Ne"),
    MBTIType.ESTJ: CognitiveStack(dominant="Te", auxiliary="Si", tertiary="Ne", inferior="Fi"),
    MBTIType.ESFJ: CognitiveStack(dominant="Fe", auxiliary="Si", tertiary="Ne", inferior="Ti"),

    # ---- SP  artisan 类型（Se 主导）----
    MBTIType.ISTP: CognitiveStack(dominant="Ti", auxiliary="Se", tertiary="Ni", inferior="Fe"),
    MBTIType.ISFP: CognitiveStack(dominant="Fi", auxiliary="Se", tertiary="Ni", inferior="Te"),
    MBTIType.ESTP: CognitiveStack(dominant="Se", auxiliary="Ti", tertiary="Fe", inferior="Ni"),
    MBTIType.ESFP: CognitiveStack(dominant="Se", auxiliary="Fi", tertiary="Te", inferior="Ni"),

    # ---- NF 理想主义者类型（Ni/Ne + Fe/Fi）----
    MBTIType.INFJ: CognitiveStack(dominant="Ni", auxiliary="Fe", tertiary="Ti", inferior="Se"),
    MBTIType.INTJ: CognitiveStack(dominant="Ni", auxiliary="Te", tertiary="Fi", inferior="Se"),
    MBTIType.ENFJ: CognitiveStack(dominant="Fe", auxiliary="Ni", tertiary="Se", inferior="Ti"),
    MBTIType.ENTJ: CognitiveStack(dominant="Te", auxiliary="Ni", tertiary="Se", inferior="Fi"),

    # ---- NT 理性者类型（Ne/Ni + Te/Ti）----
    MBTIType.INFP: CognitiveStack(dominant="Fi", auxiliary="Ne", tertiary="Si", inferior="Te"),
    MBTIType.INTP: CognitiveStack(dominant="Ti", auxiliary="Ne", tertiary="Si", inferior="Fe"),
    MBTIType.ENFP: CognitiveStack(dominant="Ne", auxiliary="Fi", tertiary="Te", inferior="Si"),
    MBTIType.ENTP: CognitiveStack(dominant="Ne", auxiliary="Ti", tertiary="Fe", inferior="Si"),
}


def _compute_dimension_scores(mbti: MBTIType) -> MBTIDimensionScore:
    """根据 MBTI 类型计算各维度得分"""
    return MBTIDimensionScore(
        energy=-40 if mbti.energy == EnergyDimension.E else 40,
        perception=-35 if mbti.perception == PerceptionDimension.S else 35,
        judgment=-30 if mbti.judgment == JudgmentDimension.T else 30,
        lifestyle=-25 if mbti.lifestyle == LifestyleDimension.J else 25,
    )


# ──────────────────────────────────────────────
# 16 型人格完整数据
# ──────────────────────────────────────────────

ALL_PERSONAS: Dict[MBTIType, MBTIPersona] = {
    MBTIType.ISTJ: MBTIPersona(
        mbti_type=MBTIType.ISTJ,
        chinese_name="检查员",
        dimension_score=_compute_dimension_scores(MBTIType.ISTJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ISTJ],
        keywords=["务实", "可靠", "条理", "传统", "细致", "责任感"],
        strengths=["执行力强", "注重细节", "可靠守信", "有条不紊"],
        weaknesses=["固执", "难以适应变化", "过度批判", "不善变通"],
        communication_style="事实导向，条理清晰，注重细节和准确性，偏好结构化表达",
    ),
    MBTIType.ISFJ: MBTIPersona(
        mbti_type=MBTIType.ISFJ,
        chinese_name="守护者",
        dimension_score=_compute_dimension_scores(MBTIType.ISFJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ISFJ],
        keywords=["温和", "负责", "体贴", "传统", "务实", "忠诚"],
        strengths=["善于关怀", "责任心强", "细致周到", "团队协作"],
        weaknesses="过度自我牺牲,难以拒绝,回避冲突,过于保守",
        communication_style="温和委婉，注重他人感受，偏好具体事例而非抽象理论",
    ),
    MBTIType.INFJ: MBTIPersona(
        mbti_type=MBTIType.INFJ,
        chinese_name="提倡者",
        dimension_score=_compute_dimension_scores(MBTIType.INFJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.INFJ],
        keywords=["洞察", "理想", "深思", "创意", "同理心", "原则"],
        strengths=["洞察力强", "有远见", "善于倾听", "坚持原则"],
        weaknesses="过于完美主义,容易倦怠,过度敏感,难以被理解",
        communication_style="隐喻丰富，关注深层意义和未来可能性，语言有感染力",
    ),
    MBTIType.INTJ: MBTIPersona(
        mbti_type=MBTIType.INTJ,
        chinese_name="建筑师",
        dimension_score=_compute_dimension_scores(MBTIType.INTJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.INTJ],
        keywords=["战略", "独立", "理性", "高效", "创新", "高标准"],
        strengths=["战略思维", "独立自主", "追求卓越", "系统性思考"],
        weaknesses="过于苛刻,不擅社交,固执己见,完美主义",
        communication_style="精确简洁，逻辑严密，直奔主题，不喜闲聊和无意义的客套",
    ),
    MBTIType.ISTP: MBTIPersona(
        mbti_type=MBTIType.ISTP,
        chinese_name="鉴赏家",
        dimension_score=_compute_dimension_scores(MBTIType.ISTP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ISTP],
        keywords=["冷静", "灵活", "实用", "探索", "独立", "动手"],
        strengths=["冷静务实", "解决问题能力强", "适应力强", "擅长分析"],
        weaknesses="不善表达情感,容易 boredom,过于随性,不喜约束",
        communication_style="简洁直接，就事论事，偏好事实和逻辑，不喜欢长篇大论",
    ),
    MBTIType.ISFP: MBTIPersona(
        mbti_type=MBTIType.ISFP,
        chinese_name="探险家",
        dimension_score=_compute_dimension_scores(MBTIType.ISFP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ISFP],
        keywords=["艺术", "敏感", "随和", "安静", "审美", "自由"],
        strengths=["审美敏锐", "善于共情", "灵活适应", "谦逊低调"],
        weaknesses="过于敏感,决策困难,回避冲突,不善规划",
        communication_style="温和感性，注重个人体验和审美表达，避免直接冲突",
    ),
    MBTIType.INFP: MBTIPersona(
        mbti_type=MBTIType.INFP,
        chinese_name="调停者",
        dimension_score=_compute_dimension_scores(MBTIType.INFP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.INFP],
        keywords=["理想", "创意", "热情", "善良", "独特", "真实"],
        strengths=["创造力强", "同理心深", "忠于价值观", "善于表达"],
        weaknesses="过于理想主义,情绪化,易自我怀疑,不擅实务",
        communication_style="情感丰富，富有诗意，关注个人价值和意义，语言有温度",
    ),
    MBTIType.INTP: MBTIPersona(
        mbti_type=MBTIType.INTP,
        chinese_name="逻辑家",
        dimension_score=_compute_dimension_scores(MBTIType.INTP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.INTP],
        keywords=["逻辑", "分析", "创新", "好奇", "独立", "理论"],
        strengths=["分析能力强", "创新思维", "理性客观", "知识渊博"],
        weaknesses="过度思考,不善执行,社交笨拙,完美拖延",
        communication_style="逻辑严密，偏好理论讨论和概念分析，喜欢提出质疑和反例",
    ),
    MBTIType.ESTP: MBTIPersona(
        mbti_type=MBTIType.ESTP,
        chinese_name="企业家",
        dimension_score=_compute_dimension_scores(MBTIType.ESTP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ESTP],
        keywords=["精力", "社交", "行动", "冒险", "说服", "灵活"],
        strengths=["行动力强", "善于社交", "随机应变", "说服力强"],
        weaknesses="缺乏耐心,冒险倾向,不拘小节,易 boredom",
        communication_style="直接有力，风趣幽默，喜欢互动和即时反馈，厌烦冗长讨论",
    ),
    MBTIType.ESFP: MBTIPersona(
        mbti_type=MBTIType.ESFP,
        chinese_name="表演者",
        dimension_score=_compute_dimension_scores(MBTIType.ESFP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ESFP],
        keywords=["热情", "开朗", "社交", "乐观", "活力", "感染力"],
        strengths=["感染力强", "善于社交", "乐观积极", "乐于助人"],
        weaknesses="容易分心,过度寻求关注,不善规划,回避深度问题",
        communication_style="热情洋溢，生动活泼，喜欢分享个人经历，有很强的感染力",
    ),
    MBTIType.ENFP: MBTIPersona(
        mbti_type=MBTIType.ENFP,
        chinese_name="活动家",
        dimension_score=_compute_dimension_scores(MBTIType.ENFP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ENFP],
        keywords=["创意", "热情", "社交", "灵感", "自由", "可能性"],
        strengths=["创意丰富", "善于激励", "人际敏锐", "适应力强"],
        weaknesses="容易分心,过度乐观,执行力弱,情绪化",
        communication_style="充满激情和想象力，喜欢头脑风暴，语言生动跳跃，感染力强",
    ),
    MBTIType.ENTP: MBTIPersona(
        mbti_type=MBTIType.ENTP,
        chinese_name="辩论家",
        dimension_score=_compute_dimension_scores(MBTIType.ENTP),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ENTP],
        keywords=["聪慧", "辩论", "创新", "挑战", "机敏", "多样"],
        strengths=["思维敏捷", "善于辩论", "创新思维", "知识面广"],
        weaknesses="好辩,缺乏执行力,容易厌倦,不拘小节",
        communication_style="善用反问和假设，喜欢抛出 provocative 观点，享受智力交锋",
    ),
    MBTIType.ESTJ: MBTIPersona(
        mbti_type=MBTIType.ESTJ,
        chinese_name="总经理",
        dimension_score=_compute_dimension_scores(MBTIType.ESTJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ESTJ],
        keywords=["果断", "高效", "条理", "领导", "务实", "可靠"],
        strengths=["领导力强", "执行力出众", "条理分明", "决策果断"],
        weaknesses="固执,不擅变通,过于强势,忽视情感",
        communication_style="直接命令式，语速较快，注重效率和结果，不耐烦绕弯子",
    ),
    MBTIType.ESFJ: MBTIPersona(
        mbti_type=MBTIType.ESFJ,
        chinese_name="执政官",
        dimension_score=_compute_dimension_scores(MBTIType.ESFJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ESFJ],
        keywords=["热情", "负责", "合作", "传统", "有条理", "关怀"],
        strengths=["组织力强", "善于关怀", "责任心强", "社交和谐"],
        weaknesses="过度在意他人看法,难以接受批评,过于传统,容易倦怠",
        communication_style="热情友善，注重群体和谐，喜欢分享经验和维护传统价值观",
    ),
    MBTIType.ENFJ: MBTIPersona(
        mbti_type=MBTIType.ENFJ,
        chinese_name="主人公",
        dimension_score=_compute_dimension_scores(MBTIType.ENFJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ENFJ],
        keywords=["魅力", "感召", "同理", "理想", "组织", "鼓舞"],
        strengths=["感召力强", "善于育人", "同理心深", "组织协调"],
        weaknesses="过度理想主义,过于讨好,容易倦怠,边界感弱",
        communication_style="富有感染力和鼓舞性，善于激发他人，语言温暖而有力量",
    ),
    MBTIType.ENTJ: MBTIPersona(
        mbti_type=MBTIType.ENTJ,
        chinese_name="指挥官",
        dimension_score=_compute_dimension_scores(MBTIType.ENTJ),
        cognitive_stack=_COGNITIVE_STACKS[MBTIType.ENTJ],
        keywords=["果断", "战略", "领导", "高效", "远见", "权威"],
        strengths=["战略眼光", "领导魅力", "执行力强", "决策迅速"],
        weaknesses="过于强势,缺乏耐心,不近人情,傲慢",
        communication_style="自信果断，目标导向，直截了当，善于规划和部署",
    ),
}
