import random
from abc import ABC, abstractmethod
from typing import Optional

from app.agent.models.action import AgentAction, ActionResult, ActionType
from app.agent.models.profile import AgentProfile
from app.agent.models.topic import Topic
from app.agent.llm.client import LLMClient, LLMResponse
from app.agent.llm.templates import PromptTemplates
from app.agent.personas.traits import ALL_TRAITS


class BaseAction(ABC):
    """
    动作执行器基类。
    每个具体动作（发帖/评论/点赞/关注）继承此类，实现 execute() 方法。
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
    ):
        self._llm = llm_client

    @abstractmethod
    def execute(
        self,
        action: AgentAction,
        agent: AgentProfile,
        topic: Topic,
    ) -> AgentAction:
        """
        执行单个动作，更新 action.result 并返回。

        Args:
            action: 要执行的动作
            agent: 执行此动作的 Agent 档案
            topic: 关联的选题

        Returns:
            更新了 result 的 action 对象
        """
        ...

    def _generate_content(
        self,
        action: AgentAction,
        agent: AgentProfile,
        topic: Topic,
        context: str = "",
    ) -> Optional[str]:
        """如果需要，调用 LLM 生成内容；无 LLM 时回落为 mock 内容"""
        if not PromptTemplates.needs_llm(action.action_type):
            return None

        if self._llm is not None:
            messages = PromptTemplates.build_messages(
                mbti_type=agent.mbti_type,
                action_type=action.action_type,
                topic=topic,
                context=context,
            )

            resp: LLMResponse = self._llm.chat(messages)

            if not resp.success:
                action.result = ActionResult.FAILED
                action.error_message = resp.error_message
                return None

            action.metadata["tokens"] = resp.usage.total_tokens
            action.metadata["cost"] = resp.usage.cost
            action.metadata["latency_ms"] = resp.latency_ms

            return resp.content

        return self._generate_mock_content(action, agent, topic, context)

    def _generate_mock_content(
        self,
        action: AgentAction,
        agent: AgentProfile,
        topic: Topic,
        context: str = "",
    ) -> str:
        """无 LLM 时生成确定性 mock 内容，确保离线可运行"""
        rng = random.Random(hash(f"{agent.agent_id}_{topic.topic_id}") & 0xFFFFFFFF)
        traits = ALL_TRAITS.get(agent.mbti_type)

        if action.action_type == ActionType.CREATE_POST:
            opening = rng.choice(traits.writing_style.typical_opening) if traits else "我觉得"
            closing = rng.choice(traits.writing_style.typical_closing) if traits else "大家怎么看？"
            catchphrase = rng.choice(traits.catchphrases) if traits else ""
            return (
                f"---TITLE---\n"
                f"【{agent.mbti_type.value}观点】{topic.title}\n"
                f"---CONTENT---\n"
                f"{opening}，关于「{topic.title}」这个话题，{topic.description}。"
                f"{catchphrase}"
                f"我认为需要从多个角度来分析这个问题。"
                f"{closing}\n"
                f"---END---"
            )
        else:
            catchphrase = rng.choice(traits.catchphrases) if traits else ""
            return f"{catchphrase} 说得很对，我也这么认为。{topic.title}确实值得深入讨论。"
