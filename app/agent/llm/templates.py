from typing import Dict, List, Optional

from app.agent.models.mbti import MBTIType
from app.agent.models.topic import Topic
from app.agent.models.action import ActionType
from app.agent.personas.prompts import PersonaPromptBuilder


# ──────────────────────────────────────────────
# API 消息模板：将 personas/prompts.py 的输出
# 转为 OpenAI-compatible message array
# ──────────────────────────────────────────────


def _format_post_title_instruction() -> str:
    return (
        "【输出格式要求】\n"
        "你输出的内容必须严格按照以下格式：\n"
        "---TITLE---\n"
        "你的帖子标题（10-30字，要吸引人）\n"
        "---CONTENT---\n"
        "你的帖子正文\n"
        "---END---\n"
        "不要包含任何其他内容。"
    )


def _format_comment_instruction() -> str:
    return (
        "【输出格式要求】\n"
        "直接输出评论内容，不要加任何前缀说明。\n"
        "不要包含标题。"
    )


_MESSAGE_TEMPLATES: Dict[ActionType, str] = {
    ActionType.CREATE_POST: _format_post_title_instruction(),
    ActionType.CREATE_COMMENT: _format_comment_instruction(),
    ActionType.REPLY_COMMENT: _format_comment_instruction(),
    ActionType.LIKE_POST: "",
    ActionType.LIKE_COMMENT: "",
    ActionType.FOLLOW_USER: "",
}


class PromptTemplates:
    """
    提示词模板仓库。
    将人格定义层 (personas/prompts.py) 的原始 Prompt 与动作类型、选题
    拼接为 LLM API 所需的 messages 格式。
    """

    @staticmethod
    def needs_llm(action_type: ActionType) -> bool:
        """判断该动作是否需要调用 LLM 生成内容"""
        return action_type in (ActionType.CREATE_POST, ActionType.CREATE_COMMENT, ActionType.REPLY_COMMENT)

    @staticmethod
    def build_messages(
        mbti_type: MBTIType,
        action_type: ActionType,
        topic: Topic,
        context: str = "",
    ) -> List[Dict[str, str]]:
        """
        构建完整的 API messages 列表。

        Args:
            mbti_type: Agent MBTI 类型
            action_type: 要执行的动作
            topic: 选题
            context: 额外上下文（目标帖子内容 / 评论内容等）

        Returns:
            符合 OpenAI API 标准的 messages 列表
        """
        system_prompt = PersonaPromptBuilder.build_system_prompt(mbti_type)

        user_prompt = PersonaPromptBuilder.build_user_prompt(
            mbti_type=mbti_type,
            action_type=action_type,
            topic=topic,
            context=context,
        )

        format_instruction = _MESSAGE_TEMPLATES.get(action_type, "")
        if format_instruction:
            user_prompt = f"{user_prompt}\n\n{format_instruction}"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def build_post_messages(
        mbti_type: MBTIType,
        topic: Topic,
    ) -> List[Dict[str, str]]:
        """构建发帖请求的 messages"""
        return PromptTemplates.build_messages(
            mbti_type=mbti_type,
            action_type=ActionType.CREATE_POST,
            topic=topic,
        )

    @staticmethod
    def build_comment_messages(
        mbti_type: MBTIType,
        post_title: str,
        post_content: str,
        topic: Topic,
    ) -> List[Dict[str, str]]:
        """构建评论请求的 messages"""
        context = f"【帖子标题】\n{post_title}\n\n【帖子内容】\n{post_content}"
        return PromptTemplates.build_messages(
            mbti_type=mbti_type,
            action_type=ActionType.CREATE_COMMENT,
            topic=topic,
            context=context,
        )

    @staticmethod
    def build_reply_messages(
        mbti_type: MBTIType,
        parent_comment: str,
        post_title: str,
        topic: Topic,
    ) -> List[Dict[str, str]]:
        """构建回复评论的 messages"""
        context = (
            f"【帖子标题】\n{post_title}\n\n"
            f"【你要回复的评论】\n{parent_comment}"
        )
        return PromptTemplates.build_messages(
            mbti_type=mbti_type,
            action_type=ActionType.REPLY_COMMENT,
            topic=topic,
            context=context,
        )

    # ── 响应解析 ──

    @staticmethod
    def parse_post_response(response_text: str) -> Dict[str, str]:
        """
        解析发帖响应，提取 title 和 content。

        期望格式：
            ---TITLE---
            帖子标题
            ---CONTENT---
            帖子正文内容
            ---END---
        """
        title = ""
        content = response_text.strip()

        if "---TITLE---" in response_text and "---CONTENT---" in response_text:
            parts = response_text.split("---CONTENT---", 1)
            title_section = parts[0]
            content_section = parts[1]

            if "---TITLE---" in title_section:
                title = title_section.split("---TITLE---", 1)[1].strip()

            content = content_section.strip()
            if content.endswith("---END---"):
                content = content[: -len("---END---")].strip()

        if not title:
            lines = content.split("\n")
            if lines:
                title = lines[0][:50]

        return {"title": title, "content": content}

    @staticmethod
    def parse_comment_response(response_text: str) -> str:
        """解析评论/回复响应，去除可能的格式标记"""
        text = response_text.strip()
        for marker in ["---CONTENT---", "---END---"]:
            if marker in text:
                text = text.replace(marker, "").strip()
        return text
