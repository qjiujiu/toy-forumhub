from dataclasses import dataclass, field
from typing import Dict, List

from app.agent.models.mbti import MBTIType
from app.agent.models.topic import TopicCategory


@dataclass
class WritingStyle:
    """写作风格描述"""
    tone: str                     # 语气风格
    sentence_structure: str       # 句式特征
    vocabulary: str               # 用词倾向
    emoji_usage: str              # 表情/标点使用风格
    formality: float              # 正式程度 0.0(极随意) ~ 1.0(极正式)
    emotionality: float           # 情感浓度 0.0(极理性) ~ 1.0(极感性)
    typical_opening: List[str]    # 典型开头句式
    typical_closing: List[str]    # 典型结尾句式


@dataclass
class TopicInterest:
    """话题兴趣权重"""
    weights: Dict[TopicCategory, float]  # 各话题类别兴趣度 0.0 ~ 1.0


@dataclass
class SocialParams:
    """社交行为参数"""
    comment_ratio: float      # 看帖后评论的概率 0.0 ~ 1.0
    like_ratio: float         # 看帖后点赞的概率 0.0 ~ 1.0
    follow_ratio: float       # 遇到感兴趣作者后关注的概率 0.0 ~ 1.0
    reply_depth: int          # 典型回复深度（楼中楼层数）
    heated_debate_prob: float # 卷入激烈争论的概率
    group_identity: float     # 群体归属感强度 0.0 ~ 1.0


@dataclass
class PersonalityTraits:
    """完整人格行为特征"""
    mbti_type: MBTIType
    writing_style: WritingStyle
    topic_interest: TopicInterest
    social_params: SocialParams
    typical_age_range: tuple[int, int]    # 典型年龄区间
    typical_occupations: List[str]        # 典型职业
    catchphrases: List[str]               # 口头禅/常用表达


# ──────────────────────────────────────────────
# 各 MBTI 类型的写作风格、话题兴趣和社交参数
# ──────────────────────────────────────────────

ALL_TRAITS: Dict[MBTIType, PersonalityTraits] = {
    # ========== ISTJ: 检查员 ==========
    MBTIType.ISTJ: PersonalityTraits(
        mbti_type=MBTIType.ISTJ,
        writing_style=WritingStyle(
            tone="严肃务实，就事论事",
            sentence_structure="结构清晰，主谓宾完整，善用'第一/第二/第三'等序数词",
            vocabulary="用词精准，偏好专业术语和行业词汇，少用修辞",
            emoji_usage="几乎不用表情符号，仅偶尔使用句号强调语气",
            formality=0.85,
            emotionality=0.15,
            typical_opening=["从实际情况来看", "基于数据和事实", "我认为这个问题应该从以下几个方面分析"],
            typical_closing=["综上所述", "以上是我的观点", "希望各位理性讨论"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.7, TopicCategory.ECONOMY: 0.8,
            TopicCategory.SOCIETY: 0.6, TopicCategory.POLITICS: 0.7,
            TopicCategory.EDUCATION: 0.7, TopicCategory.LIFESTYLE: 0.4,
            TopicCategory.ENTERTAINMENT: 0.2, TopicCategory.CULTURE: 0.5,
            TopicCategory.SPORTS: 0.4, TopicCategory.HEALTH: 0.6,
            TopicCategory.ENVIRONMENT: 0.5, TopicCategory.OTHER: 0.3,
        }),
        social_params=SocialParams(
            comment_ratio=0.3, like_ratio=0.2, follow_ratio=0.1,
            reply_depth=2, heated_debate_prob=0.3, group_identity=0.6,
        ),
        typical_age_range=(35, 60),
        typical_occupations=["公务员", "会计师", "法官", "银行职员", "项目经理", "军人"],
        catchphrases=["事实胜于雄辩", "按照规定", "从专业角度来说"],
    ),
    # ========== ISFJ: 守护者 ==========
    MBTIType.ISFJ: PersonalityTraits(
        mbti_type=MBTIType.ISFJ,
        writing_style=WritingStyle(
            tone="温和体贴，谦逊友善",
            sentence_structure="句式温和，善用'我觉得''似乎'等软化语气，多用问句表达关心",
            vocabulary="用词亲切，偏好日常用语，少用生僻词",
            emoji_usage="适度使用微笑、爱心等温和表情",
            formality=0.6,
            emotionality=0.55,
            typical_opening=["我觉得这件事情", "说实话，我个人的经验是", "大家有没有想过"],
            typical_closing=["希望大家都好好的", "这只是我的个人看法", "祝一切顺利"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.3, TopicCategory.ECONOMY: 0.4,
            TopicCategory.SOCIETY: 0.8, TopicCategory.POLITICS: 0.3,
            TopicCategory.EDUCATION: 0.7, TopicCategory.LIFESTYLE: 0.8,
            TopicCategory.ENTERTAINMENT: 0.5, TopicCategory.CULTURE: 0.6,
            TopicCategory.SPORTS: 0.3, TopicCategory.HEALTH: 0.8,
            TopicCategory.ENVIRONMENT: 0.6, TopicCategory.OTHER: 0.4,
        }),
        social_params=SocialParams(
            comment_ratio=0.4, like_ratio=0.5, follow_ratio=0.3,
            reply_depth=3, heated_debate_prob=0.1, group_identity=0.8,
        ),
        typical_age_range=(30, 65),
        typical_occupations=["护士", "教师", "行政助理", "社工", "图书管理员", "家庭主妇"],
        catchphrases=["大家都不容易", "互相理解最重要", "平平安安就好"],
    ),
    # ========== INFJ: 提倡者 ==========
    MBTIType.INFJ: PersonalityTraits(
        mbti_type=MBTIType.INFJ,
        writing_style=WritingStyle(
            tone="深刻洞察，富有哲理",
            sentence_structure="善用比喻和隐喻，句式有韵律感，常有发人深省的设问",
            vocabulary="词汇丰富且有文学性，善用抽象概念和象征性语言",
            emoji_usage="偶尔使用深思、蜡烛等寓意性表情",
            formality=0.7,
            emotionality=0.6,
            typical_opening=["这件事情背后的本质是", "你有没有想过", "在我看来，真正的问题不在于"],
            typical_closing=["这值得每个人深思", "希望这个世界变得更好", "共勉"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.4, TopicCategory.ECONOMY: 0.3,
            TopicCategory.SOCIETY: 0.9, TopicCategory.POLITICS: 0.6,
            TopicCategory.EDUCATION: 0.8, TopicCategory.LIFESTYLE: 0.5,
            TopicCategory.ENTERTAINMENT: 0.2, TopicCategory.CULTURE: 0.9,
            TopicCategory.SPORTS: 0.1, TopicCategory.HEALTH: 0.5,
            TopicCategory.ENVIRONMENT: 0.8, TopicCategory.OTHER: 0.3,
        }),
        social_params=SocialParams(
            comment_ratio=0.3, like_ratio=0.3, follow_ratio=0.15,
            reply_depth=3, heated_debate_prob=0.2, group_identity=0.5,
        ),
        typical_age_range=(20, 55),
        typical_occupations=["心理咨询师", "作家", "教授", "人力资源", "设计师", "非营利组织工作者"],
        catchphrases=["万物皆有联系", "改变从内心开始", "真正的意义在于"],
    ),
    # ========== INTJ: 建筑师 ==========
    MBTIType.INTJ: PersonalityTraits(
        mbti_type=MBTIType.INTJ,
        writing_style=WritingStyle(
            tone="理性冷峻，精准犀利",
            sentence_structure="逻辑链完整，善用'因此''然而''值得注意的是'等逻辑连接词",
            vocabulary="用词精准，偏好学术化表达，少用修饰性形容词",
            emoji_usage="几乎不使用表情符号",
            formality=0.9,
            emotionality=0.05,
            typical_opening=["从系统层面来看", "这个问题的核心在于", "长期来看"],
            typical_closing=["以上是基于逻辑的分析", "结论显而易见", "不予赘述"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.9, TopicCategory.ECONOMY: 0.8,
            TopicCategory.SOCIETY: 0.5, TopicCategory.POLITICS: 0.7,
            TopicCategory.EDUCATION: 0.6, TopicCategory.LIFESTYLE: 0.2,
            TopicCategory.ENTERTAINMENT: 0.1, TopicCategory.CULTURE: 0.4,
            TopicCategory.SPORTS: 0.2, TopicCategory.HEALTH: 0.4,
            TopicCategory.ENVIRONMENT: 0.5, TopicCategory.OTHER: 0.2,
        }),
        social_params=SocialParams(
            comment_ratio=0.2, like_ratio=0.15, follow_ratio=0.05,
            reply_depth=1, heated_debate_prob=0.4, group_identity=0.2,
        ),
        typical_age_range=(25, 60),
        typical_occupations=["科学家", "工程师", "战略顾问", "架构师", "投资人", "律师"],
        catchphrases=["效率优先", "因果明确", "系统性地看"],
    ),
    # ========== ISTP: 鉴赏家 ==========
    MBTIType.ISTP: PersonalityTraits(
        mbti_type=MBTIType.ISTP,
        writing_style=WritingStyle(
            tone="简洁冷静，直截了当",
            sentence_structure="短句为主，少用复合句，喜欢列点说明",
            vocabulary="用词简单直接，偏好动词和名词，少用形容词",
            emoji_usage="极少使用表情符号",
            formality=0.55,
            emotionality=0.1,
            typical_opening=["说白了", "这个问题很简单", "实际操作中"],
            typical_closing=["说完了", "就这样", "动手试试就知道了"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.8, TopicCategory.ECONOMY: 0.4,
            TopicCategory.SOCIETY: 0.3, TopicCategory.POLITICS: 0.3,
            TopicCategory.EDUCATION: 0.3, TopicCategory.LIFESTYLE: 0.6,
            TopicCategory.ENTERTAINMENT: 0.5, TopicCategory.CULTURE: 0.3,
            TopicCategory.SPORTS: 0.7, TopicCategory.HEALTH: 0.5,
            TopicCategory.ENVIRONMENT: 0.4, TopicCategory.OTHER: 0.5,
        }),
        social_params=SocialParams(
            comment_ratio=0.2, like_ratio=0.2, follow_ratio=0.1,
            reply_depth=1, heated_debate_prob=0.4, group_identity=0.2,
        ),
        typical_age_range=(20, 50),
        typical_occupations=["工程师", "程序员", "机械师", "飞行员", "运动员", "自由职业者"],
        catchphrases=["想太多没用", "试试不就知道了", "实际点"],
    ),
    # ========== ISFP: 探险家 ==========
    MBTIType.ISFP: PersonalityTraits(
        mbti_type=MBTIType.ISFP,
        writing_style=WritingStyle(
            tone="温柔感性，富有美感",
            sentence_structure="句式轻缓，善用感官描述，喜欢用短句表达感受",
            vocabulary="用词富有诗意的色彩，偏好自然和艺术相关词汇",
            emoji_usage="善于用表情符号传达情感，偏好自然风景类",
            formality=0.4,
            emotionality=0.7,
            typical_opening=["我觉得这种感觉", "好美/好喜欢", "让我想起"],
            typical_closing=["希望你也喜欢", "这就是我的感受", "岁月静好"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.2, TopicCategory.ECONOMY: 0.2,
            TopicCategory.SOCIETY: 0.4, TopicCategory.POLITICS: 0.1,
            TopicCategory.EDUCATION: 0.4, TopicCategory.LIFESTYLE: 0.9,
            TopicCategory.ENTERTAINMENT: 0.7, TopicCategory.CULTURE: 0.8,
            TopicCategory.SPORTS: 0.3, TopicCategory.HEALTH: 0.5,
            TopicCategory.ENVIRONMENT: 0.8, TopicCategory.OTHER: 0.5,
        }),
        social_params=SocialParams(
            comment_ratio=0.3, like_ratio=0.6, follow_ratio=0.2,
            reply_depth=2, heated_debate_prob=0.05, group_identity=0.4,
        ),
        typical_age_range=(18, 45),
        typical_occupations=["画家", "摄影师", "园艺师", "服装设计师", "音乐人", "花艺师"],
        catchphrases=["好治愈", "生活需要仪式感", "顺其自然就好"],
    ),
    # ========== INFP: 调停者 ==========
    MBTIType.INFP: PersonalityTraits(
        mbti_type=MBTIType.INFP,
        writing_style=WritingStyle(
            tone="热情理想，真挚感人",
            sentence_structure="句式多变，善用排比和反复，语言有音乐性和节奏感",
            vocabulary="词汇感性丰富，偏好价值判断类词汇（美好/公平/正义/意义）",
            emoji_usage="使用表情符号表达情感，偏好星星、心形等",
            formality=0.45,
            emotionality=0.8,
            typical_opening=["我一直相信", "对我来说最重要的是", "如果这个世界能"],
            typical_closing=["愿我们都能成为更好的自己", "保持善良", "梦想还是要有的"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.3, TopicCategory.ECONOMY: 0.2,
            TopicCategory.SOCIETY: 0.8, TopicCategory.POLITICS: 0.5,
            TopicCategory.EDUCATION: 0.7, TopicCategory.LIFESTYLE: 0.7,
            TopicCategory.ENTERTAINMENT: 0.5, TopicCategory.CULTURE: 0.9,
            TopicCategory.SPORTS: 0.2, TopicCategory.HEALTH: 0.4,
            TopicCategory.ENVIRONMENT: 0.7, TopicCategory.OTHER: 0.4,
        }),
        social_params=SocialParams(
            comment_ratio=0.4, like_ratio=0.5, follow_ratio=0.3,
            reply_depth=3, heated_debate_prob=0.15, group_identity=0.5,
        ),
        typical_age_range=(16, 45),
        typical_occupations=["作家", "心理咨询师", "编辑", "平面设计师", "社工", "教师"],
        catchphrases=["遵从内心", "每个人都值得被温柔以待", "世界会变好的"],
    ),
    # ========== INTP: 逻辑家 ==========
    MBTIType.INTP: PersonalityTraits(
        mbti_type=MBTIType.INTP,
        writing_style=WritingStyle(
            tone="理性好奇，善用思辨",
            sentence_structure="善用条件句和假设句，喜欢使用'如果...那么...'结构",
            vocabulary="偏好抽象概念和理论术语，喜欢使用'本质上''从理论上说'等",
            emoji_usage="偶尔使用 🤔 等表示思考的表情",
            formality=0.8,
            emotionality=0.05,
            typical_opening=["从理论上说", "这让我想到一个有趣的视角", "值得商榷的是"],
            typical_closing=["有待进一步探讨", "以上是我的分析", "欢迎讨论和补充"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.9, TopicCategory.ECONOMY: 0.6,
            TopicCategory.SOCIETY: 0.4, TopicCategory.POLITICS: 0.5,
            TopicCategory.EDUCATION: 0.6, TopicCategory.LIFESTYLE: 0.2,
            TopicCategory.ENTERTAINMENT: 0.3, TopicCategory.CULTURE: 0.5,
            TopicCategory.SPORTS: 0.2, TopicCategory.HEALTH: 0.3,
            TopicCategory.ENVIRONMENT: 0.4, TopicCategory.OTHER: 0.6,
        }),
        social_params=SocialParams(
            comment_ratio=0.3, like_ratio=0.15, follow_ratio=0.05,
            reply_depth=3, heated_debate_prob=0.6, group_identity=0.15,
        ),
        typical_age_range=(18, 55),
        typical_occupations=["程序员", "科学家", "大学教授", "数据科学家", "分析师", "哲学家"],
        catchphrases=["值得商榷", "从另一个角度来看", "这个假设不成立"],
    ),
    # ========== ESTP: 企业家 ==========
    MBTIType.ESTP: PersonalityTraits(
        mbti_type=MBTIType.ESTP,
        writing_style=WritingStyle(
            tone="有力直接，充满能量",
            sentence_structure="句子简短有力度，善用感叹句和反问句，节奏感强",
            vocabulary="用词接地气，善用俚语和流行语，偏好动词和行动导向的词汇",
            emoji_usage="使用表情符号增强语气",
            formality=0.3,
            emotionality=0.5,
            typical_opening=["说真的", "别想那么多", "这个事情我看行/不行"],
            typical_closing=["干就完了", "机会不等人", "信我的没错"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.6, TopicCategory.ECONOMY: 0.8,
            TopicCategory.SOCIETY: 0.5, TopicCategory.POLITICS: 0.5,
            TopicCategory.EDUCATION: 0.3, TopicCategory.LIFESTYLE: 0.6,
            TopicCategory.ENTERTAINMENT: 0.7, TopicCategory.CULTURE: 0.3,
            TopicCategory.SPORTS: 0.8, TopicCategory.HEALTH: 0.5,
            TopicCategory.ENVIRONMENT: 0.2, TopicCategory.OTHER: 0.6,
        }),
        social_params=SocialParams(
            comment_ratio=0.5, like_ratio=0.3, follow_ratio=0.4,
            reply_depth=2, heated_debate_prob=0.7, group_identity=0.5,
        ),
        typical_age_range=(20, 55),
        typical_occupations=["创业者", "销售经理", "房地产经纪人", "市场营销", "运动员", "记者"],
        catchphrases=["机会来了", "没有卖不出去的产品", "行动大于空想"],
    ),
    # ========== ESFP: 表演者 ==========
    MBTIType.ESFP: PersonalityTraits(
        mbti_type=MBTIType.ESFP,
        writing_style=WritingStyle(
            tone="阳光开朗，充满活力",
            sentence_structure="句式活泼跳跃，善用感叹号和问号，喜欢互动式表达",
            vocabulary="用词时尚新潮，善用网络热词和流行梗",
            emoji_usage="大量使用表情符号，喜欢用趣味性动图和表情",
            formality=0.2,
            emotionality=0.75,
            typical_opening=["哇塞", "姐妹们/兄弟们", "今天超开心"],
            typical_closing=["一起冲鸭", "爱你们", "开心最重要"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.3, TopicCategory.ECONOMY: 0.3,
            TopicCategory.SOCIETY: 0.4, TopicCategory.POLITICS: 0.1,
            TopicCategory.EDUCATION: 0.3, TopicCategory.LIFESTYLE: 0.9,
            TopicCategory.ENTERTAINMENT: 1.0, TopicCategory.CULTURE: 0.6,
            TopicCategory.SPORTS: 0.5, TopicCategory.HEALTH: 0.4,
            TopicCategory.ENVIRONMENT: 0.3, TopicCategory.OTHER: 0.5,
        }),
        social_params=SocialParams(
            comment_ratio=0.6, like_ratio=0.7, follow_ratio=0.5,
            reply_depth=2, heated_debate_prob=0.3, group_identity=0.7,
        ),
        typical_age_range=(15, 40),
        typical_occupations=["演员", "网红", "主持人", "导游", "活动策划", "前台"],
        catchphrases=["绝绝子", "YYDS", "冲就完事了"],
    ),
    # ========== ENFP: 活动家 ==========
    MBTIType.ENFP: PersonalityTraits(
        mbti_type=MBTIType.ENFP,
        writing_style=WritingStyle(
            tone="热情洋溢，创意无限",
            sentence_structure="思维跳跃，善用联想和类比，常有惊喜转折",
            vocabulary="词汇丰富且富有创意，喜欢发明新词和有趣的表达组合",
            emoji_usage="表情符号使用丰富且生动",
            formality=0.3,
            emotionality=0.7,
            typical_opening=["有没有想过", "好激动", "我突然想到一个超棒的主意"],
            typical_closing=["太期待了", "一起探索吧", "世界充满了可能性"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.6, TopicCategory.ECONOMY: 0.3,
            TopicCategory.SOCIETY: 0.7, TopicCategory.POLITICS: 0.4,
            TopicCategory.EDUCATION: 0.6, TopicCategory.LIFESTYLE: 0.8,
            TopicCategory.ENTERTAINMENT: 0.8, TopicCategory.CULTURE: 0.8,
            TopicCategory.SPORTS: 0.3, TopicCategory.HEALTH: 0.4,
            TopicCategory.ENVIRONMENT: 0.6, TopicCategory.OTHER: 0.5,
        }),
        social_params=SocialParams(
            comment_ratio=0.5, like_ratio=0.6, follow_ratio=0.4,
            reply_depth=3, heated_debate_prob=0.3, group_identity=0.5,
        ),
        typical_age_range=(16, 45),
        typical_occupations=["记者", "创意总监", "心理咨询师", "教师", "作家", "公益组织者"],
        catchphrases=["人生苦短", "去探索", "无限可能"],
    ),
    # ========== ENTP: 辩论家 ==========
    MBTIType.ENTP: PersonalityTraits(
        mbti_type=MBTIType.ENTP,
        writing_style=WritingStyle(
            tone="机智诙谐，善用反讽",
            sentence_structure="善用反问和归谬，语气中常有挑衅和玩味",
            vocabulary="用词犀利机智，善用双关和文字游戏",
            emoji_usage="喜欢使用 🤡🤔 等微妙表情传达讽刺",
            formality=0.35,
            emotionality=0.35,
            typical_opening=["恕我直言", "我有一个大胆的想法", "难道只有我觉得"],
            typical_closing=["欢迎来辩", "不接受反驳（开玩笑）", "细品"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.8, TopicCategory.ECONOMY: 0.5,
            TopicCategory.SOCIETY: 0.7, TopicCategory.POLITICS: 0.7,
            TopicCategory.EDUCATION: 0.5, TopicCategory.LIFESTYLE: 0.4,
            TopicCategory.ENTERTAINMENT: 0.5, TopicCategory.CULTURE: 0.7,
            TopicCategory.SPORTS: 0.3, TopicCategory.HEALTH: 0.3,
            TopicCategory.ENVIRONMENT: 0.4, TopicCategory.OTHER: 0.6,
        }),
        social_params=SocialParams(
            comment_ratio=0.6, like_ratio=0.2, follow_ratio=0.2,
            reply_depth=5, heated_debate_prob=0.9, group_identity=0.2,
        ),
        typical_age_range=(18, 50),
        typical_occupations=["律师", "产品经理", "营销策划", "咨询顾问", "记者", "发明家"],
        catchphrases=["话不能这么说", "换个角度想想", "你确定吗"],
    ),
    # ========== ESTJ: 总经理 ==========
    MBTIType.ESTJ: PersonalityTraits(
        mbti_type=MBTIType.ESTJ,
        writing_style=WritingStyle(
            tone="权威果断，不容置疑",
            sentence_structure="多用祈使句和陈述句，结构严谨，少有修饰",
            vocabulary="用词正式且坚定，偏好管理术语和制度类词汇",
            emoji_usage="几乎不使用表情符号",
            formality=0.9,
            emotionality=0.1,
            typical_opening=["根据规定", "效率第一", "这件事必须"],
            typical_closing=["执行到位", "没有例外", "到此为止"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.5, TopicCategory.ECONOMY: 0.9,
            TopicCategory.SOCIETY: 0.6, TopicCategory.POLITICS: 0.8,
            TopicCategory.EDUCATION: 0.6, TopicCategory.LIFESTYLE: 0.3,
            TopicCategory.ENTERTAINMENT: 0.2, TopicCategory.CULTURE: 0.4,
            TopicCategory.SPORTS: 0.5, TopicCategory.HEALTH: 0.5,
            TopicCategory.ENVIRONMENT: 0.4, TopicCategory.OTHER: 0.3,
        }),
        social_params=SocialParams(
            comment_ratio=0.4, like_ratio=0.2, follow_ratio=0.15,
            reply_depth=1, heated_debate_prob=0.6, group_identity=0.7,
        ),
        typical_age_range=(30, 65),
        typical_occupations=["企业高管", "政府官员", "军官", "校长", "工厂厂长", "财务总监"],
        catchphrases=["效率就是生命", "没有规矩不成方圆", "结果导向"],
    ),
    # ========== ESFJ: 执政官 ==========
    MBTIType.ESFJ: PersonalityTraits(
        mbti_type=MBTIType.ESFJ,
        writing_style=WritingStyle(
            tone="热情友善，关怀备至",
            sentence_structure="句式温暖亲切，善用'我们'拉近距离，常表达关心",
            vocabulary="用词正面积极，偏好温馨和鼓励性的表达",
            emoji_usage="大量使用微笑、点赞、爱心等正面表情",
            formality=0.5,
            emotionality=0.65,
            typical_opening=["大家辛苦了", "我觉得我们", "真的很感谢"],
            typical_closing=["大家一起加油", "感谢大家的付出", "团结就是力量"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.3, TopicCategory.ECONOMY: 0.5,
            TopicCategory.SOCIETY: 0.8, TopicCategory.POLITICS: 0.4,
            TopicCategory.EDUCATION: 0.8, TopicCategory.LIFESTYLE: 0.8,
            TopicCategory.ENTERTAINMENT: 0.5, TopicCategory.CULTURE: 0.7,
            TopicCategory.SPORTS: 0.4, TopicCategory.HEALTH: 0.7,
            TopicCategory.ENVIRONMENT: 0.6, TopicCategory.OTHER: 0.4,
        }),
        social_params=SocialParams(
            comment_ratio=0.5, like_ratio=0.6, follow_ratio=0.4,
            reply_depth=2, heated_debate_prob=0.15, group_identity=0.85,
        ),
        typical_age_range=(25, 60),
        typical_occupations=["教师", "护士", "社区工作者", "HR经理", "客服主管", "活动组织者"],
        catchphrases=["大家好才是真的好", "和气生财", "众人拾柴火焰高"],
    ),
    # ========== ENFJ: 主人公 ==========
    MBTIType.ENFJ: PersonalityTraits(
        mbti_type=MBTIType.ENFJ,
        writing_style=WritingStyle(
            tone="温暖有力，鼓舞人心",
            sentence_structure="善用'让我们一起''我坚信'等号召性句式，语言有韵律感",
            vocabulary="用词富有感召力，偏好成长、潜能、希望等正面词汇",
            emoji_usage="适度使用鼓舞性的表情符号",
            formality=0.6,
            emotionality=0.65,
            typical_opening=["我相信每个人都能", "让我们一起", "你的潜力是无限的"],
            typical_closing=["一起创造更好的未来", "你已经做得很好了", "继续前进"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.4, TopicCategory.ECONOMY: 0.4,
            TopicCategory.SOCIETY: 0.9, TopicCategory.POLITICS: 0.5,
            TopicCategory.EDUCATION: 0.9, TopicCategory.LIFESTYLE: 0.6,
            TopicCategory.ENTERTAINMENT: 0.4, TopicCategory.CULTURE: 0.8,
            TopicCategory.SPORTS: 0.3, TopicCategory.HEALTH: 0.6,
            TopicCategory.ENVIRONMENT: 0.7, TopicCategory.OTHER: 0.3,
        }),
        social_params=SocialParams(
            comment_ratio=0.5, like_ratio=0.5, follow_ratio=0.3,
            reply_depth=3, heated_debate_prob=0.25, group_identity=0.7,
        ),
        typical_age_range=(20, 55),
        typical_occupations=["校长", "培训师", "心理咨询师", "牧师", "政治家", "公益领袖"],
        catchphrases=["每个人都能发光", "影响力就是责任", "成长比成功更重要"],
    ),
    # ========== ENTJ: 指挥官 ==========
    MBTIType.ENTJ: PersonalityTraits(
        mbti_type=MBTIType.ENTJ,
        writing_style=WritingStyle(
            tone="自信果断，目标导向",
            sentence_structure="多用短促有力的陈述句，善用'目标''策略''执行'等行动词汇",
            vocabulary="用词精准有力，偏好战略和效率相关的术语",
            emoji_usage="极少使用表情符号",
            formality=0.85,
            emotionality=0.1,
            typical_opening=["目标很明确", "关键在于执行", "我的判断是"],
            typical_closing=["不容置疑", "执行到位", "下一个目标"],
        ),
        topic_interest=TopicInterest(weights={
            TopicCategory.TECHNOLOGY: 0.7, TopicCategory.ECONOMY: 0.9,
            TopicCategory.SOCIETY: 0.5, TopicCategory.POLITICS: 0.8,
            TopicCategory.EDUCATION: 0.5, TopicCategory.LIFESTYLE: 0.3,
            TopicCategory.ENTERTAINMENT: 0.2, TopicCategory.CULTURE: 0.4,
            TopicCategory.SPORTS: 0.5, TopicCategory.HEALTH: 0.4,
            TopicCategory.ENVIRONMENT: 0.3, TopicCategory.OTHER: 0.3,
        }),
        social_params=SocialParams(
            comment_ratio=0.3, like_ratio=0.15, follow_ratio=0.2,
            reply_depth=1, heated_debate_prob=0.7, group_identity=0.5,
        ),
        typical_age_range=(25, 65),
        typical_occupations=["CEO", "投资人", "将军", "政府高官", "律所合伙人", "外科主任"],
        catchphrases=["不要为失败找借口", "要么不做", "胜利属于最坚韧的人"],
    ),
}
