from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """LLM API 配置"""
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.8
    max_tokens: int = 2048
    request_timeout: int = 120
    max_retries: int = 3


@dataclass
class PopulationConfig:
    """人群采样配置"""
    seed: int = 42                 # 随机种子，确保可复现
    default_agent_count: int = 100  # 默认 Agent 池规模


@dataclass
class SimulationConfig:
    """模拟行为配置"""
    post_ratio: float = 0.2        # 参与者中发帖比例
    comment_ratio: float = 0.4     # 参与者中评论比例（基于帖子数）
    like_ratio: float = 0.6        # 参与者中点赞比例
    follow_ratio: float = 0.1      # 参与者中关注比例
    max_comments_per_post: int = 5 # 每篇帖子的最大评论数


@dataclass
class AgentConfig:
    """Agent 子系统全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    population: PopulationConfig = field(default_factory=PopulationConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)

    def update_llm(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """便捷更新 LLM 配置"""
        if api_key is not None:
            self.llm.api_key = api_key
        if base_url is not None:
            self.llm.base_url = base_url
        if model is not None:
            self.llm.model = model
