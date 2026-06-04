"""
Agent 舆情模拟启动脚本
======================
使用方式：
    python scripts/run_agent_simulation.py

流程：
    1. 连接 MySQL → 初始化 Repositories + Services
    2. 按 MBTI 比例创建 50 个 Agent 用户
    3. 创建一个选题
    4. 执行完整模拟（发帖→评论→点赞→关注）
    5. 打印结果
"""

import sys
import os

# 确保项目根目录在 Python path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# ─── 数据库 & Service 依赖 ───
from app.storage.v2.database import SessionLocal
from app.storage.v2.user.SQLAlchemyUserRepository import SQLAlchemyUserRepository
from app.storage.v2.post.SQLAlchemyPostRepository import SQLAlchemyPostRepository
from app.storage.v2.comment.SQLAlchemyCommentRepository import SQLAlchemyCommentRepository
from app.storage.v2.follow.SQLAlchemyFollowRepository import SQLAlchemyFollowRepository
from app.storage.v2.like.SQLAlchemyLikeRepository import SQLAlchemyLikeRepository

from app.service.v2.user_svc import UserService
from app.service.v2.post_svc import PostService
from app.service.v2.comment_svc import CommentService
from app.service.v2.like_svc import LikeService
from app.service.v2.follow_svc import FollowService

from app.schemas.v2.user import UserCreate
from app.schemas.v2.post import PostCreate, PostDto
from app.schemas.v2.comment import CommentCreate
from app.schemas.v2.like import LikeCreate
from app.schemas.v2.follow import FollowCreate
from app.models.v2.like import LikeTargetType
from app.models.v2.post import PostVisibility, PostPublishStatus

# ─── Agent 系统 ───
from app.agent import (
    AgentConfig, AgentOrchestrator, LLMClient,
    Topic, TopicCategory,
)
from app.agent.population.generator import AgentGenerator


def main():
    # ==============================
    # 1. 初始化数据库 + Services
    # ==============================
    print("=" * 60)
    print("1. 连接数据库，初始化 Services")
    print("=" * 60)

    db = SessionLocal()
    user_repo = SQLAlchemyUserRepository(db)
    post_repo = SQLAlchemyPostRepository(db)
    comment_repo = SQLAlchemyCommentRepository(db)
    like_repo = SQLAlchemyLikeRepository(db)
    follow_repo = SQLAlchemyFollowRepository(db)

    user_svc = UserService(user_repo)
    post_svc = PostService(post_repo, user_repo)
    comment_svc = CommentService(comment_repo, post_repo, user_repo)
    like_svc = LikeService(like_repo, post_repo, comment_repo)
    follow_svc = FollowService(follow_repo, user_repo)

    # ==============================
    # 2. 配置 LLM（从 .env 读取 DeepSeek API Key）
    # ==============================
    from dotenv import load_dotenv
    load_dotenv()
    import os

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if api_key:
        llm = LLMClient(api_key=api_key, model="deepseek-chat")
        print(f"  LLM 已配置: deepseek-chat")
    else:
        llm = None
        print("  [警告] 未找到 DEEPSEEK_API_KEY，将使用 mock 内容")

    # ==============================
    # 3. 构造 Orchestrator + 回调
    # ==============================
    print("=" * 60)
    print("2. 构造 AgentOrchestrator")
    print("=" * 60)

    def create_forum_user(username: str, password: str, phone: str) -> str:
        """AgentGenerator 回调：在论坛中创建真实用户，返回 uid"""
        data = UserCreate(username=username, password=password, phone=phone)
        result = user_svc.create_user(data, to_dict=True)
        uid = result["uid"]
        print(f"  [创建用户] {username} → uid={uid}")
        return uid

    def create_post(author_uid: str, title: str, content: str) -> str:
        """PostAction 回调：创建帖子，返回 pid"""
        data = PostCreate(
            author_id=author_uid,
            title=title,
            content=content,
            post_status=PostDto(
                visibility=PostVisibility.PUBLIC,
                publish_status=PostPublishStatus.PUBLISHED,
            ),
        )
        result = post_svc.create_post(data, to_dict=True)
        pid = result["pid"]
        print(f"  [发帖] {title[:20]}... → pid={pid}")
        return pid

    def create_comment(author_uid: str, post_pid: str, content: str, parent_cid: str = None) -> str:
        """CommentAction 回调：创建评论，返回 cid"""
        data = CommentCreate(
            author_id=author_uid,
            post_id=post_pid,
            content=content,
            parent_id=parent_cid,
            root_id=parent_cid,  # 一级评论 root_id = parent_id
        )
        result = comment_svc.create_comment(data, to_dict=True)
        cid = result["cid"] if isinstance(result, dict) else result
        print(f"  [评论] → cid={cid}")
        return cid

    def like_target(user_uid: str, target_type_code: int, target_id: str) -> bool:
        """LikeAction 回调：点赞"""
        data = LikeCreate(
            user_id=user_uid,
            target_type=LikeTargetType(target_type_code),
            target_id=target_id,
        )
        like_svc.like(data)
        print(f"  [点赞] user={user_uid[:8]} target={target_id[:8]}")
        return True

    def follow_user(user_uid: str, followed_uid: str) -> bool:
        """FollowAction 回调：关注用户"""
        data = FollowCreate(user_id=user_uid, followed_user_id=followed_uid)
        follow_svc.follow(data)
        print(f"  [关注] {user_uid[:8]} → {followed_uid[:8]}")
        return True

    agent_gen = AgentGenerator(create_user_callback=create_forum_user)

    # 创建 Orchestrator
    orch = AgentOrchestrator(
        llm_client=llm,
        agent_generator=agent_gen,
        create_post_fn=create_post,
        create_comment_fn=create_comment,
        like_fn=like_target,
        follow_fn=follow_user,
    )

    # ==============================
    # 4. 初始化 Agent 池
    # ==============================
    print("=" * 60)
    print("3. 初始化 Agent 池（按 MBTI 比例创建 50 个论坛用户）")
    print("=" * 60)

    agents = orch.initialize_agents(count=50)
    print(f"  共创建 {len(agents)} 个 Agent，分布：")
    from collections import Counter
    type_counts = Counter(a.mbti_type.value for a in agents)
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")

    # ==============================
    # 5. 创建选题 & 执行模拟
    # ==============================
    print("=" * 60)
    print("4. 创建选题并执行模拟")
    print("=" * 60)

    topic = Topic(
        topic_id="sim_001",
        title="LGBT群体在中国应该收到保护和支持吗",
        description="探讨 LGBT 少数群体的生存状况"
                    "以及人们如何对待这一群体",
        category=TopicCategory.TECHNOLOGY,
        agent_count=20,   # 从 Agent 池中抽取 20 人参与
        post_count=3,     # 预期发帖 3 篇
        comment_depth=2,
        duration_hours=48,
    )

    result = orch.run_topic(topic)

    # ==============================
    # 6. 结果汇总
    # ==============================
    print("=" * 60)
    print("5. 模拟结果")
    print("=" * 60)
    print(f"  选题：{result.topic.title}")
    print(f"  总动作数：{result.total_count}")
    print(f"  成功：{result.success_count}")
    print(f"  失败：{result.failed_count}")
    print(f"  ── 发帖：{len(result.posts_created)} 篇")
    print(f"  ── 评论：{len(result.comments_created)} 条")
    print(f"  ── 点赞：{len(result.likes_done)} 次")
    print(f"  ── 关注：{len(result.follows_done)} 次")
    if result.total_tokens > 0:
        print(f"  LLM Token 消耗：{result.total_tokens}")
        print(f"  预估费用：CNY {result.total_cost:.4f}")

    # 打印帖子详情
    if result.posts_created:
        print()
        print("  帖子列表：")
        for action in result.posts_created:
            title = action.title or "(无标题)"
            content_preview = (action.content or "")[:60].replace("\n", " ")
            mbti = "?"
            agent = orch._agent_gen.get_by_agent_id(action.agent_id)
            if agent:
                mbti = agent.mbti_type.value
            safe_title = title.encode("gbk", errors="replace").decode("gbk", errors="replace")
            safe_content = content_preview.encode("gbk", errors="replace").decode("gbk", errors="replace")
            print(f"    [{mbti}] {safe_title}")
            print(f"      {safe_content}...")

    # ==============================
    # 7. 清理
    # ==============================
    db.close()
    print()
    print("[OK] 模拟完成！数据库连接已关闭。")


if __name__ == "__main__":
    main()
