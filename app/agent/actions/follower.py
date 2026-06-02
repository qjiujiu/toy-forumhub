import logging
from typing import Callable, Optional
from datetime import datetime

from app.agent.models.action import AgentAction, ActionResult
from app.agent.models.profile import AgentProfile
from app.agent.models.topic import Topic
from app.agent.actions.base import BaseAction

logger = logging.getLogger(__name__)

# 关注回调：接收 (user_uid, followed_user_uid) 返回是否成功
FollowUserFn = Callable[[str, str], bool]


class FollowAction(BaseAction):
    """
    关注执行器。
    关注不需要 LLM 生成内容，直接调用论坛 Service。
    """

    def __init__(
        self,
        follow_fn: Optional[FollowUserFn] = None,
    ):
        super().__init__(llm_client=None)
        self._follow = follow_fn

    def execute(
        self,
        action: AgentAction,
        agent: AgentProfile,
        topic: Topic,
    ) -> AgentAction:
        target_uid = action.target_id or "unknown"
        logger.info(f"[FollowAction] Agent {agent.agent_id} following user '{target_uid}'")

        if self._follow is not None:
            try:
                ok = self._follow(agent.user_uid, target_uid)
                if ok:
                    action.result = ActionResult.SUCCESS
                else:
                    action.result = ActionResult.FAILED
                    action.error_message = "Follow returned False (already following or target gone)"
                action.executed_at = datetime.now()
            except Exception as e:
                action.result = ActionResult.FAILED
                action.error_message = str(e)
                logger.error(f"[FollowAction] Failed to follow: {e}")
        else:
            action.result = ActionResult.SUCCESS
            action.executed_at = datetime.now()

        return action
