import uuid
import logging
from typing import Callable, Dict, List, Optional

from app.agent.config import AgentConfig
from app.agent.models.mbti import MBTIType
from app.agent.models.profile import AgentProfile
from app.agent.models.action import AgentAction, ActionType, ActionResult
from app.agent.models.topic import Topic

from app.agent.population.sampler import MBTISampler
from app.agent.population.generator import AgentGenerator
from app.agent.llm.client import LLMClient
from app.agent.llm.templates import PromptTemplates

from app.agent.actions.base import BaseAction
from app.agent.actions.poster import PostAction, CreatePostFn
from app.agent.actions.commenter import CommentAction, CreateCommentFn
from app.agent.actions.liker import LikeAction, LikeTargetFn
from app.agent.actions.follower import FollowAction, FollowUserFn
from app.models.v2.like import LikeTargetType

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    总调度器，编排全流程：选题 → 采样 → 计划 → 生成 → 执行。

    使用方式：
        1. 创建 Topic
        2. 初始化 Agent 池（AgentGenerator）
        3. 注入论坛 Service 回调
        4. 调用 run_topic(topic) 执行模拟

    Usage:
        orch = AgentOrchestrator(
            llm_client=LLMClient(api_key="sk-xxx"),
            create_post_fn=post_service.create_post,
            create_comment_fn=comment_service.create_comment,
            like_fn=like_service.like,
            follow_fn=follow_service.follow,
        )
        result = orch.run_topic(topic)
        print(result.summary())
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        # LLM
        llm_client: Optional[LLMClient] = None,
        # 论坛 Service 回调（可选，不传则使用模拟模式）
        create_post_fn: Optional[CreatePostFn] = None,
        create_comment_fn: Optional[CreateCommentFn] = None,
        like_fn: Optional[LikeTargetFn] = None,
        follow_fn: Optional[FollowUserFn] = None,
        # Agent 池（可选，不传会自动生成）
        agent_generator: Optional[AgentGenerator] = None,
    ):
        self.config = config or AgentConfig()

        # LLM
        if llm_client is not None:
            self._llm = llm_client
        elif self.config.llm.api_key:
            self._llm = LLMClient(
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url,
                model=self.config.llm.model,
                timeout=self.config.llm.request_timeout,
                max_retries=self.config.llm.max_retries,
            )
        else:
            self._llm = None

        # 采样器
        self._sampler = MBTISampler(seed=self.config.population.seed)

        # Agent 池
        if agent_generator is not None:
            self._agent_gen = agent_generator
        else:
            self._agent_gen = AgentGenerator()

        # 动作执行器
        self._poster = PostAction(llm_client=self._llm, create_post_fn=create_post_fn)
        self._commenter = CommentAction(llm_client=self._llm, create_comment_fn=create_comment_fn)
        self._liker = LikeAction(like_fn=like_fn)
        self._follower = FollowAction(follow_fn=follow_fn)

    # ─────────────────────────────────────────
    # 初始化 Agent 池
    # ─────────────────────────────────────────

    def initialize_agents(self, count: Optional[int] = None) -> List[AgentProfile]:
        """初始化 Agent 池：采样 → 生成"""
        n = count or self.config.population.default_agent_count
        mbti_types = self._sampler.sample(n)
        agents = self._agent_gen.generate_all(mbti_types)
        logger.info(
            f"[Orchestrator] Initialized {len(agents)} agents "
            f"({len(set(mbti_types))} MBTI types)"
        )
        return agents

    # ─────────────────────────────────────────
    # 核心：执行选题模拟
    # ─────────────────────────────────────────

    def run_topic(self, topic: Topic) -> "SimulationResult":
        """
        执行一个选题的完整模拟。

        流程：
        1. 从 Agent 池采样参与者
        2. 生成行为计划
        3. 按顺序执行：发帖 → 评论 → 点赞 → 关注
        4. 返回模拟结果
        """
        logger.info(f"[Orchestrator] Running topic: '{topic.title}' ({topic.topic_id})")

        # 1) 采样参与者
        participants = self._sample_participants(topic)

        # 2) 生成计划
        plan = self._create_plan(topic, participants)

        # 3) 分阶段执行
        results = self._execute_plan(topic, participants, plan)

        # 4) 汇总
        summary = SimulationResult(topic=topic, actions=results)
        logger.info(f"[Orchestrator] Topic done: {summary.success_count} success / {summary.total_count} total")
        return summary

    def _sample_participants(self, topic: Topic) -> List[AgentProfile]:
        """从 Agent 池采样参与者"""
        active = self._agent_gen.list_active()
        if not active:
            logger.warning("[Orchestrator] No active agents. Run initialize_agents() first.")
            return []

        # 按 MBTI 比例从活跃 Agent 中采样
        pool: Dict[MBTIType, List[str]] = {}
        for agent in active:
            pool.setdefault(agent.mbti_type, []).append(agent.agent_id)

        sampled_items = self._sampler.sample_from_pool(pool, topic.agent_count)
        sampled_ids = {aid for _, aid in sampled_items}
        return [a for a in active if a.agent_id in sampled_ids]

    def _create_plan(
        self,
        topic: Topic,
        participants: List[AgentProfile],
    ) -> List[AgentAction]:
        """生成行为计划"""
        cfg = self.config.simulation
        actions: List[AgentAction] = []

        if not participants:
            return actions

        # 计算各角色数量
        n_posters = max(1, int(len(participants) * cfg.post_ratio))
        n_remaining = len(participants) - n_posters

        # 分配角色
        import random
        rng = random.Random(self.config.population.seed + hash(topic.topic_id) % (2 ** 16))
        shuffled = participants[:]
        rng.shuffle(shuffled)

        posters = shuffled[:n_posters]
        commenters = shuffled[n_posters:n_posters + max(1, int(n_remaining * cfg.comment_ratio))]
        likers = shuffled[max(0, n_posters - 2):n_posters + max(1, int(n_remaining * (cfg.comment_ratio + cfg.like_ratio)))]
        followers = shuffled[-max(1, int(len(participants) * cfg.follow_ratio)):]

        # 发帖计划
        posts_per_agent = max(1, topic.post_count // max(1, len(posters)))
        for agent in posters:
            for _ in range(posts_per_agent):
                actions.append(AgentAction(
                    action_id=str(uuid.uuid4()),
                    agent_id=agent.agent_id,
                    action_type=ActionType.CREATE_POST,
                    topic_id=topic.topic_id,
                ))

        # 评论、点赞、关注计划在 _execute_plan 中动态创建（需要帖子 pid）
        # 先存起来供后续阶段使用
        self._pending_commenters = commenters
        self._pending_likers = likers
        self._pending_followers = followers

        return actions

    def _execute_plan(
        self,
        topic: Topic,
        participants: List[AgentProfile],
        plan: List[AgentAction],
    ) -> List[AgentAction]:
        """分阶段执行行为计划"""
        agent_map = {a.agent_id: a for a in participants}
        results: List[AgentAction] = []

        # 阶段 1：发帖
        post_results = self._execute_batch(self._poster, plan, agent_map, topic)
        results.extend(post_results)

        # 收集成功创建的帖子
        successful_pids = [
            a.target_id for a in post_results
            if a.result == ActionResult.SUCCESS and a.target_id
        ]

        if not successful_pids:
            logger.warning("[Orchestrator] No posts created, skipping subsequent actions")
            return results

        # 阶段 2：评论
        # 构建 pid → 帖子内容的映射，让评论 Agent 能看到它正在回复什么
        post_contents = {
            a.target_id: (a.title, a.content)
            for a in post_results
            if a.result == ActionResult.SUCCESS and a.target_id
        }
        comment_actions = self._build_comment_actions(successful_pids, post_contents, topic, agent_map)
        if comment_actions:
            comment_results = self._execute_batch(self._commenter, comment_actions, agent_map, topic)
            results.extend(comment_results)

        # 收集成功创建的评论
        successful_cids = [
            a.metadata.get("comment_cid") for a in comment_results
            if a.result == ActionResult.SUCCESS and a.metadata.get("comment_cid")
        ]

        # 阶段 3：点赞
        like_actions = self._build_like_actions(successful_pids, successful_cids, topic, agent_map)
        if like_actions:
            like_results = self._execute_batch(self._liker, like_actions, agent_map, topic)
            results.extend(like_results)

        # 阶段 4：关注
        follow_actions = self._build_follow_actions(successful_pids, topic, agent_map, post_results)
        if follow_actions:
            follow_results = self._execute_batch(self._follower, follow_actions, agent_map, topic)
            results.extend(follow_results)

        return results

    def _execute_batch(
        self,
        executor: BaseAction,
        actions: List[AgentAction],
        agent_map: Dict[str, AgentProfile],
        topic: Topic,
    ) -> List[AgentAction]:
        """批量执行同一类动作"""
        for action in actions:
            agent = agent_map.get(action.agent_id)
            if agent is None:
                action.result = ActionResult.FAILED
                action.error_message = "Agent not found"
                continue
            executor.execute(action, agent, topic)
        return actions

    def _build_comment_actions(
        self,
        post_pids: List[str],
        post_contents: Dict[str, tuple[str, str]],
        topic: Topic,
        agent_map: Dict[str, AgentProfile],
    ) -> List[AgentAction]:
        """为每个帖子创建评论动作，附带帖子标题和内容供 LLM 参考"""
        actions = []
        commenters = getattr(self, "_pending_commenters", [])
        cfg = self.config.simulation

        for pid in post_pids:
            title, content = post_contents.get(pid, ("", ""))
            for agent in commenters[:cfg.max_comments_per_post]:
                actions.append(AgentAction(
                    action_id=str(uuid.uuid4()),
                    agent_id=agent.agent_id,
                    action_type=ActionType.CREATE_COMMENT,
                    topic_id=topic.topic_id,
                    target_id=pid,
                    metadata={
                        "post_title": title,
                        "post_content": content,
                    },
                ))
        return actions

    def _build_like_actions(
        self,
        post_pids: List[str],
        comment_cids: List[str],
        topic: Topic,
        agent_map: Dict[str, AgentProfile],
    ) -> List[AgentAction]:
        actions = []
        likers = getattr(self, "_pending_likers", [])

        for pid in post_pids:
            for agent in likers[:3]:
                actions.append(AgentAction(
                    action_id=str(uuid.uuid4()),
                    agent_id=agent.agent_id,
                    action_type=ActionType.LIKE_POST,
                    topic_id=topic.topic_id,
                    target_id=pid,
                    metadata={"target_type_code": LikeTargetType.POST.value},
                ))
        for cid in comment_cids:
            for agent in likers[:3]:
                actions.append(AgentAction(
                    action_id=str(uuid.uuid4()),
                    agent_id=agent.agent_id,
                    action_type=ActionType.LIKE_POST,
                    topic_id=topic.topic_id,
                    target_id=cid,
                    metadata={"target_type_code": LikeTargetType.COMMENT.value},
                ))
        return actions

    def _build_follow_actions(
        self,
        post_pids: List[str],
        topic: Topic,
        agent_map: Dict[str, AgentProfile],
        post_results: List[AgentAction],
    ) -> List[AgentAction]:
        """为帖子作者创建关注动作"""
        actions = []
        followers = getattr(self, "_pending_followers", [])

        author_uids = set()
        for action in post_results:
            if action.result == ActionResult.SUCCESS:
                agent = agent_map.get(action.agent_id)
                if agent:
                    author_uids.add(agent.user_uid)

        for agent in followers:
            for target_uid in list(author_uids)[:3]:
                if agent.user_uid != target_uid:
                    actions.append(AgentAction(
                        action_id=str(uuid.uuid4()),
                        agent_id=agent.agent_id,
                        action_type=ActionType.FOLLOW_USER,
                        topic_id=topic.topic_id,
                        target_id=target_uid,
                    ))
        return actions


class SimulationResult:
    """模拟结果汇总"""

    def __init__(self, topic: Topic, actions: List[AgentAction]):
        self.topic = topic
        self.actions = actions

    @property
    def total_count(self) -> int:
        return len(self.actions)

    @property
    def success_count(self) -> int:
        return sum(1 for a in self.actions if a.result == ActionResult.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for a in self.actions if a.result == ActionResult.FAILED)

    @property
    def posts_created(self) -> List[AgentAction]:
        return [a for a in self.actions if a.action_type == ActionType.CREATE_POST and a.result == ActionResult.SUCCESS]

    @property
    def comments_created(self) -> List[AgentAction]:
        return [a for a in self.actions if a.action_type in (ActionType.CREATE_COMMENT, ActionType.REPLY_COMMENT) and a.result == ActionResult.SUCCESS]

    @property
    def likes_done(self) -> List[AgentAction]:
        return [a for a in self.actions if a.action_type in (ActionType.LIKE_POST, ActionType.LIKE_COMMENT) and a.result == ActionResult.SUCCESS]

    @property
    def follows_done(self) -> List[AgentAction]:
        return [a for a in self.actions if a.action_type == ActionType.FOLLOW_USER and a.result == ActionResult.SUCCESS]

    @property
    def total_tokens(self) -> int:
        return sum(a.metadata.get("tokens", 0) for a in self.actions)

    @property
    def total_cost(self) -> float:
        return sum(a.metadata.get("cost", 0.0) for a in self.actions)

    def summary(self) -> str:
        return (
            f"Topic: {self.topic.title}\n"
            f"  Posts: {len(self.posts_created)}\n"
            f"  Comments: {len(self.comments_created)}\n"
            f"  Likes: {len(self.likes_done)}\n"
            f"  Follows: {len(self.follows_done)}\n"
            f"  Success: {self.success_count}/{self.total_count}\n"
            f"  Tokens: {self.total_tokens}, Cost: ¥{self.total_cost:.4f}"
        )
