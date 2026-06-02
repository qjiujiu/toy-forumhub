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

# 评论回调：接收 (author_uid, post_pid, content, parent_cid) 返回评论 cid
CreateCommentFn = Callable[[str, str, str, Optional[str]], str]


class CommentAction(BaseAction):
    """
    评论执行器。
    调用 LLM 生成评论内容 → 通过回调创建论坛评论 → 记录结果。
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        create_comment_fn: Optional[CreateCommentFn] = None,
    ):
        super().__init__(llm_client)
        self._create_comment = create_comment_fn

    def execute(
        self,
        action: AgentAction,
        agent: AgentProfile,
        topic: Topic,
    ) -> AgentAction:
        logger.info(
            f"[CommentAction] Agent {agent.agent_id} commenting on "
            f"post/comment '{action.target_id}'"
        )

        # 1) 构建上下文
        context_parts = []
        if action.metadata.get("post_title"):
            context_parts.append(f"【帖子标题】\n{action.metadata['post_title']}")
        if action.metadata.get("post_content"):
            context_parts.append(f"【帖子内容】\n{action.metadata['post_content']}")
        context = "\n\n".join(context_parts)

        # 2) LLM 生成内容
        content = self._generate_content(action, agent, topic, context=context)
        if content is None and action.result == ActionResult.FAILED:
            return action

        body = PromptTemplates.parse_comment_response(content or "")
        if not body:
            action.result = ActionResult.FAILED
            action.error_message = "LLM returned empty comment"
            return action

        action.content = body

        # 3) 调用论坛 Service 创建评论
        if self._create_comment is not None:
            try:
                parent_id = action.target_id if action.action_type == ActionType.REPLY_COMMENT else None
                cid = self._create_comment(agent.user_uid, action.target_id, body, parent_id)
                action.metadata["comment_cid"] = cid
                action.result = ActionResult.SUCCESS
                action.executed_at = datetime.now()
                logger.info(f"[CommentAction] Comment created: cid={cid}")
            except Exception as e:
                action.result = ActionResult.FAILED
                action.error_message = str(e)
                logger.error(f"[CommentAction] Failed to create comment: {e}")
        else:
            action.metadata["comment_cid"] = f"mock_cid_{agent.agent_id[:8]}"
            action.result = ActionResult.SUCCESS
            action.executed_at = datetime.now()

        return action
