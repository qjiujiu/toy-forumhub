import logging
from typing import Callable, Optional
from datetime import datetime

from app.agent.models.action import AgentAction, ActionResult
from app.agent.models.profile import AgentProfile
from app.agent.models.topic import Topic
from app.agent.actions.base import BaseAction

logger = logging.getLogger(__name__)

# 点赞回调：接收 (user_uid, target_type_code, target_id) 返回是否成功
LikeTargetFn = Callable[[str, int, str], bool]


class LikeAction(BaseAction):
    """
    点赞执行器。
    点赞不需要 LLM 生成内容，直接调用论坛 Service。
    """

    def __init__(
        self,
        like_fn: Optional[LikeTargetFn] = None,
    ):
        super().__init__(llm_client=None)
        self._like = like_fn

    def execute(
        self,
        action: AgentAction,
        agent: AgentProfile,
        topic: Topic,
    ) -> AgentAction:
        target_desc = action.target_id or "unknown"
        logger.info(f"[LikeAction] Agent {agent.agent_id} liking target '{target_desc}'")

        if self._like is not None:
            try:
                target_type = action.metadata.get("target_type_code", 0)
                ok = self._like(agent.user_uid, target_type, action.target_id)
                if ok:
                    action.result = ActionResult.SUCCESS
                else:
                    action.result = ActionResult.FAILED
                    action.error_message = "Like returned False (already liked or target gone)"
                action.executed_at = datetime.now()
            except Exception as e:
                action.result = ActionResult.FAILED
                action.error_message = str(e)
                logger.error(f"[LikeAction] Failed to like: {e}")
        else:
            action.result = ActionResult.SUCCESS
            action.executed_at = datetime.now()

        return action
