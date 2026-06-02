"""
AI Agent 智能体模拟子系统
==========================
用于舆情模拟的智能体论坛系统，通过 MBTI 人格矩阵驱动的 AI Agent 模拟真实用户行为。
"""

from app.agent.config import AgentConfig, LLMConfig, PopulationConfig, SimulationConfig
from app.agent.manager import AgentOrchestrator, SimulationResult
from app.agent.population import MBTISampler, AgentGenerator
from app.agent.llm import LLMClient, PromptTemplates
from app.agent.models import MBTIType, Topic, TopicCategory, ActionType

__all__ = [
    "AgentConfig", "LLMConfig", "PopulationConfig", "SimulationConfig",
    "AgentOrchestrator", "SimulationResult",
    "MBTISampler", "AgentGenerator",
    "LLMClient", "PromptTemplates",
    "MBTIType", "Topic", "TopicCategory", "ActionType",
]
