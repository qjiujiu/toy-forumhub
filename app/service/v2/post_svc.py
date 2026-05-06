from typing import List

from app.schemas.v2.post import PostCreate, PostOut, BatchPostsOut, PostStatus, PostUpdate, TopPostOut
from app.schemas.v2.post_content import PostContentUpdate
from app.schemas.v2.user import UserRole

from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.user.user_interface import IUserRepository

from app.core.logx import logger
from app.core.exceptions import PostNotFound, ForbiddenAction, AdminPermissionDenied, UserNotFound


class PostService:
    def __init__(
        self,
        post_repo: IPostRepository,
        user_repo: IUserRepository,
    ):
        self._post_repo = post_repo
        self._user_repo = user_repo

    def _verify_admin(self, uid: str) -> None:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        if user.user_info.role != UserRole.ADMIN:
            raise AdminPermissionDenied(f"user {uid} is not an admin")

    def create_post(self, data: PostCreate) -> PostOut:
        # 业务层视角：创建帖子是一件事情。
        # 存储层视角：需要写入三张表（posts/post_contents/post_stats）。
        # 这里通过“聚合仓储” create_post 把多表细节隐藏起来。
        post_out = self._post_repo.create_post(data)
        logger.info(f"[CREATE_POST] Created post aggregate pid={post_out.pid} for author={data.author_id}")
        return post_out

    def get_post(self, pid: str) -> PostOut:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        return post_out

    def get_posts_by_author(
        self,
        author_id: str,
        page: int = 0,
        page_size: int = 10,
    ) -> BatchPostsOut:
        result = self._post_repo.get_by_author(author_id, page, page_size)
        return result

    def update_post_content(
        self,
        uid: str,
        pid: str,
        data: PostContentUpdate,
    ) -> PostOut:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        if post_out.author_id != uid:
            raise ForbiddenAction(f"user {uid} cannot update post {pid}")

        ok = self._post_repo.update_content(pid, data)
        if not ok:
            # 理论上不应该发生：“post 存在但是 content 不存在” 这种情况, 这种属于数据不一致。
            raise PostNotFound(f"post {pid} content not found")
        logger.info(f"[UPDATE_POST_CONTENT] Updated content for pid={pid} by user={uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        if not updated_post:
            raise PostNotFound(f"post {pid} not found")
        return updated_post

    def update_post_visibility(
        self,
        uid: str,
        pid: str,
        data: PostUpdate,
    ) -> PostOut:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        if post_out.author_id != uid:
            raise ForbiddenAction(f"user {uid} cannot update post {pid}")

        self._post_repo.update(pid, PostStatus(visibility=data.visibility))
        logger.info(f"[UPDATE_POST_VISIBILITY] Updated visibility for pid={pid} by user={uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        if not updated_post:
            raise PostNotFound(f"post {pid} not found")
        return updated_post

    def ban_post(
        self,
        admin_uid: str,
        pid: str,
    ) -> PostOut:
        self._verify_admin(admin_uid)

        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")

        self._post_repo.update(pid, PostStatus(publish_status=2))
        logger.info(f"[BAN_POST] Banned post pid={pid} by admin={admin_uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        if not updated_post:
            raise PostNotFound(f"post {pid} not found")
        return updated_post

    def publish_post(
        self,
        uid: str,
        pid: str,
    ) -> PostOut:
        post_out = self._post_repo.get_by_pid(pid)
        if not post_out:
            raise PostNotFound(f"post {pid} not found")
        if post_out.author_id != uid:
            raise ForbiddenAction(f"user {uid} cannot update post {pid}")

        current_status = post_out.post_status.publish_status
        if current_status != 0:
            raise ForbiddenAction(f"only draft posts can be published")

        self._post_repo.update(pid, PostStatus(publish_status=1))
        logger.info(f"[PUBLISH_POST] Published post pid={pid} by user={uid}")

        updated_post = self._post_repo.get_by_pid(pid)
        if not updated_post:
            raise PostNotFound(f"post {pid} not found")
        return updated_post

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

    def get_top_liked_posts(self, limit: int = 10) -> List[TopPostOut]:
        items = self._post_repo.get_top_liked_with_posts(limit)
        return items

    def get_top_commented_posts(self, limit: int = 10) -> List[TopPostOut]:
        items = self._post_repo.get_top_commented_with_posts(limit)
        return items
