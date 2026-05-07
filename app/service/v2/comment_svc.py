from typing import Dict, List, Optional, Union

from app.schemas.v2.comment import CommentCreate, CommentOnlyCreate, CommentOut, BatchCommentsOut, CommentQuery, StatusUpdate
from app.schemas.v2.post import PostOut

from app.storage.v2.comment.comment_interface import ICommentRepository
from app.storage.v2.post.post_interface import IPostRepository
from app.storage.v2.user.user_interface import IUserRepository

from app.schemas.v2.user import UserRole

from app.core.logx import logger
from app.core.exceptions import CommentNotFound, UserNotFound, AdminPermissionDenied


class CommentService:

    def __init__(
        self,
        comment_repo: ICommentRepository,
        post_repo: IPostRepository,
        user_repo: IUserRepository,
    ):
        self._comment_repo = comment_repo
        self._post_repo = post_repo
        self._user_repo = user_repo

    def _verify_admin(self, uid: str) -> None:
        user = self._user_repo.find_user(uid=uid)
        if not user:
            raise UserNotFound(f"user {uid} not found")
        if user.user_info.role != UserRole.ADMIN:
            raise AdminPermissionDenied(f"user {uid} is not an admin")

    def create_comment(self, data: CommentCreate, to_dict: bool = True) -> Union[Dict, str]:
        # 验证帖子存在
        post = self._post_repo.get_by_pid(data.post_id)
        if not post:
            raise ValueError(f"post {data.post_id} not found")

        comment_out = self._comment_repo.create_comment(data)
        logger.info(f"[CREATE_COMMENT] Created comment cid={comment_out.cid} for post={data.post_id}")

        if to_dict:
            return comment_out.model_dump()
        return comment_out.cid

    def get_comment(self, cid: str) -> Optional[CommentOut]:
        return self._comment_repo.get_by_cid(cid)

    def get_comments(
        self,
        query: CommentQuery,
        page: int = 0,
        page_size: int = 20,
    ) -> BatchCommentsOut:
        return self._comment_repo.get_comments(query, page, page_size)

    def update_comment(self, admin_uid: str, cid: str, data: StatusUpdate) -> bool:
        self._verify_admin(admin_uid)
        return self._comment_repo.update(cid, data)

    def delete_comment(self, cid: str) -> bool:
        return self._comment_repo.soft_delete(cid)

    def hard_delete_comment(self, admin_uid: str, cid: str) -> bool:
        self._verify_admin(admin_uid)
        comment = self._comment_repo.get_by_cid(cid)
        if not comment:
            raise CommentNotFound(f"comment {cid} not found")
        self._comment_repo.hard_delete(cid)
        logger.info(f"[HARD_DELETE_COMMENT] Hard deleted comment cid={cid} by admin={admin_uid}")
        return True

    def get_post_by_comment_cid(self, cid: str, to_dict: bool = True) -> Union[Dict, PostOut]:
        comment = self._comment_repo.get_by_cid(cid)
        if not comment:
            raise CommentNotFound(f"comment {cid} not found")
        post = self._post_repo.get_by_pid(comment.post_id)
        return post.model_dump() if to_dict and post else post
