from typing import Dict, Optional, Union

from app.schemas.post import (
    PostCreate,
    PostOnlyCreate,
    PostOut,
    PostReviewOut,
    BatchPostsOut,
    PostUpdate,
    PostReviewUpdate,
    PostReviewStatus,
    PostReviewOut,
    BatchPostsReviewOut,
    PostAdminOut,
    BatchPostsAdminOut,
    PostGet,
)
from app.schemas.post_content import (
    PostContentCreate,
    PostContentOut,
)
from app.schemas.post_stats import (
    PostStatsCreate,
    PostStatsOut,
)

from app.storage.post.post_interface import IPostRepository
from app.storage.post_content.post_content_interface import IPostContentRepository
from app.storage.post_stats.post_stats_interface import IPostStatsRepository
from app.storage.user.user_interface import IUserRepository

from app.core.logx import logger
from app.core.exceptions import PostNotFound, InvalidReviewStatusTransition, UserNotFound
import json
from redis import Redis
from fastapi.encoders import jsonable_encoder


class PostService:

    def __init__(
        self,
        user_repo: IUserRepository,
        post_repo: IPostRepository,
        content_repo: IPostContentRepository,
        stats_repo: IPostStatsRepository,
    ):
        """
        初始化用户服务
        
        Args:
            user_repo: 用户仓储实例
            stats_repo: 用户统计仓储实例
            follow_repo: 关注仓储实例（可选，用于硬删除）
        """
        self._user_repo = user_repo
        self._stats_repo = stats_repo
        self._content_repo = content_repo
        self._post_repo = post_repo
        self._POST_CACHE_KEY_PATTERN = "post:{pid}"     # 缓存 key 模板
        self._POST_CACHE_TTL_SECONDS = 60 * 5           # 缓存过期时间 5 分钟，可自行调整
    
    def create_post(self, data: PostCreate, to_dict: bool = True,) -> Union[Dict, PostOut]:
        """
        创建帖子（业务接口）：
        1. 查看 用户ID 是否存在
        2. 在 posts 表创建一条记录
        3. 在 post_contents 表创建对应的标题 + 内容
        4. 在 post_stats 表创建统计记录（like_count=0, comment_count=0）
        5. 返回组装好的 PostOut
        """
        # 1. 查看 用户ID 是否存在
        user = self._user_repo.get_user_by_uid(data.author_id)
        if not user:
            raise UserNotFound(f"user {data.author_id} not found")
        
        # 2. 创建 posts 基本记录
        post_only = PostOnlyCreate(
            author_id=data.author_id,
            visibility=data.visibility,
            publish_status=data.publish_status,
        )
        pid = self._post_repo.create_post(post_only)
        logger.info(f"Created post pid={pid} for author={data.author_id}")

        # 3. 创建内容记录
        content_create = PostContentCreate(
            post_id=pid,
            title=data.title,
            content=data.content,
        )
        self._content_repo.create(content_create)
        logger.info(f"Created post_content for pid={pid}")

        # 4. 创建统计记录（点赞数、评论数初始化为 0）
        stats_create = PostStatsCreate(post_id=pid)
        self._stats_repo.create(stats_create)
        logger.info(f"Initialized post_stats for pid={pid}")

        # 5. 使用仓库封装的 get_post_by_pid 返回完整结构（含内容 + 统计）
        post_out = self._post_repo.author_get_post_by_pid(pid = pid, author_id= data.author_id)
        if not post_out:
            # 理论上不应该发生，防御性处理
            raise PostNotFound(f"post {pid} not found after creation")

        return post_out.model_dump() if to_dict else post_out