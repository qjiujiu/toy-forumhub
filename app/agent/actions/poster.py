import logging
from typing import Callable, Optional
from datetime import datetime

from app.agent.models.action import AgentAction, ActionResult, ActionType
from app.agent.models.profile import AgentProfile
from app.agent.models.topic import Topic
from app.agent.llm.client import LLMClient
from app.agent.llm.templates import PromptTemplates
from app.agent.actions.base import BaseAction

logger = logging.getLogger(__name__)

# 发帖回调：接收 (author_uid, title, content) 返回帖子 pid
CreatePostFn = Callable[[str, str, str], str]


class PostAction(BaseAction):
    """
    发帖执行器。
    调用 LLM 生成标题+正文 → 通过回调创建论坛帖子 → 记录结果。
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        create_post_fn: Optional[CreatePostFn] = None,
    ):
        super().__init__(llm_client)
        self._create_post = create_post_fn

    def execute(
        self,
        action: AgentAction,
        agent: AgentProfile,
        topic: Topic,
    ) -> AgentAction:
        logger.info(f"[PostAction] Agent {agent.agent_id} creating post on topic '{topic.title}'")

        # 1) LLM 生成内容
        content = self._generate_content(action, agent, topic)
        if content is None and action.result == ActionResult.FAILED:
            return action

        # 2) 解析标题和正文
        parsed = PromptTemplates.parse_post_response(content or "")
        title = parsed["title"]
        body = parsed["content"]

        if not title or not body:
            action.result = ActionResult.FAILED
            action.error_message = "LLM returned empty title or content"
            return action

        action.title = title
        action.content = body

        # 3) 调用论坛 Service 创建帖子
        if self._create_post is not None:
            try:
                pid = self._create_post(agent.user_uid, title, body)
                action.target_id = pid
                action.result = ActionResult.SUCCESS
                action.executed_at = datetime.now()
                logger.info(f"[PostAction] Post created: pid={pid}")
            except Exception as e:
                action.result = ActionResult.FAILED
                action.error_message = str(e)
                logger.error(f"[PostAction] Failed to create post: {e}")
        else:
            # 无回调时标记成功，便于离线测试
            action.target_id = f"mock_pid_{agent.agent_id[:8]}"
            action.result = ActionResult.SUCCESS
            action.executed_at = datetime.now()

        return action
