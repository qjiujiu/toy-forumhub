from typing import Dict, List, Optional, Union

from app.schemas.v2.post import PostCreate, PostOnlyCreate, PostOut, BatchPostsOut, PostDto, PostUpdate, TopPostsResponse, TopPostOut
from app.schemas.v2.post_content import PostContentCreate, PostContentUpdate
from app.schemas.v2.post_stats import PostStatsCreate, PostStatsDto
from app.schemas.v2.user import UserRole

from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.post_content.post_content_interface import IPostContentRepository
from app.storage.v2.post_stats.post_stats_interface import IPostStatsRepository
from app.storage.v2.user.user_interface import IUserRepository

from app.core.logx import logger
from app.core.exceptions import PostNotFound, ForbiddenAction, AdminPermissionDenied, UserNotFound


class PostService:

    def __init__(
        self,
        post_repo: IPostRepository,
        content_repo: IPostContentRepository,
        stats_repo: IPostStatsRepository,
        user_repo: IUserRepository,
    ):
        self._post_repo = post_repo
        self._content_repo = content_repo
        self._stats_repo = stats_repo
        self._user_repo = user_repo

    def _verify_admin(self, uid: str) -> None:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        if user.user_info.role != UserRole.ADMIN:
            raise AdminPermissionDenied(f"user {uid} is not an admin")

    def create_post(self, data: PostCreate, to_dict: bool = True) -> Union[Dict, PostOut]:
        pid = self._post_repo.create(PostOnlyCreate.model_validate(data))
        logger.info(f"[CREATE_POST] Created post pid={pid} for author={data.author_id}")

        content_create = PostContentCreate(
            post_id=pid,
            title=data.title,
            content=data.content,
        )
        self._content_repo.create(content_create)
        logger.info(f"[CREATE_POST] Created post_content for pid={pid}")

        stats_create = PostStatsCreate(
            post_id=pid,
            post_stats=PostStatsDto(),
        )
        self._stats_repo.create(stats_create)
        logger.info(f"[CREATE_POST] Initialized post_stats for pid={pid}")

        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found after creation")

        return post_out.model_dump() if to_dict else post_out

    def get_post(self, pid: str, to_dict: bool = True) -> Union[Dict, PostOut]:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        return post_out.model_dump() if to_dict else post_out

    def get_posts_by_author(
        self,
        author_id: str,
        page: int = 0,
        page_size: int = 10,
        to_dict: bool = True,
    ) -> Union[Dict, BatchPostsOut]:
        result = self._post_repo.get_by_author(author_id, page, page_size)
        return result.model_dump() if to_dict else result

    def update_post_content(
        self,
        uid: str,
        pid: str,
        data: PostContentUpdate,
        to_dict: bool = True,
    ) -> Union[Dict, PostOut]:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        if post_out.author_id != uid:
            raise ForbiddenAction(f"user {uid} cannot update post {pid}")

        self._content_repo.update(pid, data)
        logger.info(f"[UPDATE_POST_CONTENT] Updated content for pid={pid} by user={uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        return updated_post.model_dump() if to_dict else updated_post

    def update_post_visibility(
        self,
        uid: str,
        pid: str,
        data: PostUpdate,
        to_dict: bool = True,
    ) -> Union[Dict, PostOut]:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        if post_out.author_id != uid:
            raise ForbiddenAction(f"user {uid} cannot update post {pid}")

        self._post_repo.update(pid, PostDto(visibility=data.visibility))
        logger.info(f"[UPDATE_POST_VISIBILITY] Updated visibility for pid={pid} by user={uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        return updated_post.model_dump() if to_dict else updated_post

    def ban_post(
        self,
        admin_uid: str,
        pid: str,
        to_dict: bool = True,
    ) -> Union[Dict, PostOut]:
        self._verify_admin(admin_uid)

        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")

        self._post_repo.update(pid, PostDto(publish_status=2))
        logger.info(f"[BAN_POST] Banned post pid={pid} by admin={admin_uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        return updated_post.model_dump() if to_dict else updated_post

    def publish_post(
        self,
        uid: str,
        pid: str,
        to_dict: bool = True,
    ) -> Union[Dict, PostOut]:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        if post_out.author_id != uid:
            raise ForbiddenAction(f"user {uid} cannot update post {pid}")

        current_status = post_out.post_status.publish_status
        if current_status != 0:
            raise ForbiddenAction(f"only draft posts can be published")

        self._post_repo.update(pid, PostDto(publish_status=1))
        logger.info(f"[PUBLISH_POST] Published post pid={pid} by user={uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        return updated_post.model_dump() if to_dict else updated_post

    def soft_delete_post(
        self,
        uid: str,
        pid: str,
    ) -> bool:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        if post_out.author_id != uid:
            raise ForbiddenAction(f"user {uid} cannot delete post {pid}")

        self._post_repo.soft_delete(pid)
        logger.info(f"[SOFT_DELETE] Soft deleted post pid={pid} by user={uid}")
        return True

    def hard_delete_post(
        self,
        admin_uid: str,
        pid: str,
    ) -> bool:
        self._verify_admin(admin_uid)

        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")

        self._post_repo.hard_delete(pid)
        logger.info(f"[HARD_DELETE] Hard deleted post pid={pid} by admin={admin_uid}")
        return True

    def get_top_liked_posts(self, limit: int = 10, to_dict: bool = True) -> Union[Dict, List[TopPostOut]]:
        items = self._stats_repo.get_top_liked_with_posts(limit)
        return [i.model_dump() for i in items] if to_dict else items

    def get_top_commented_posts(self, limit: int = 10, to_dict: bool = True) -> Union[Dict, List[TopPostOut]]:
        items = self._stats_repo.get_top_commented_with_posts(limit)
        return [i.model_dump() for i in items] if to_dict else items