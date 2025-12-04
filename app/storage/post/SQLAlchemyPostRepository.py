from typing import Optional, List
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.post import Post, PostReviewStatus, PostPublishStatus, PostVisibility

from app.schemas.post import (
    PostOnlyCreate,
    PostOut,
    PostReviewOut,
    BatchPostsOut,
    PostUpdate,
    PostReviewUpdate,
    BatchPostsReviewOut,
    PostGet,
    PostAdminOut,
    BatchPostsAdminOut
)
from app.core.exceptions import ForbiddenAction
from app.storage.post.post_interface import IPostRepository
from app.core.db import transaction

from app.core.logx import logger

# 东八区时区（如果你希望 deleted_at / reviewed_at 使用东八区时间）
CN_TZ = timezone(timedelta(hours=8))


class SQLAlchemyPostRepository(IPostRepository):
    """
    使用 SQLAlchemy 实现的帖子仓库
    业务层依赖 IPostRepository 抽象接口
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- 内部基础查询 ----------
    
    def _viewer_query(self):
        """
        访客 / 其他用户查看帖子时使用：
        只返回「对他人可见」的帖子：
        - 未软删
        - 已发布
        - 审核通过
        - 可见性为公开（PUBLIC）
        """
        return (
            self.db.query(Post)
            .filter(
                Post.deleted_at.is_(None),
                Post.publish_status == PostPublishStatus.PUBLISHED.value,
                Post.review_status == PostReviewStatus.APPROVED.value,
                Post.visibility == PostVisibility.PUBLIC.value,
            )
        )

    def _author_query(self, author_id: str):
        """
        作者自己查看自己的帖子：
        - 未软删
        - 不限制 publish_status（草稿也能看）
        - 不限制 review_status（待审/拒绝也能看）
        - 不限制 visibility（仅作者可见当然可以看到）
        """
        return (self.db.query(Post).filter(Post.deleted_at.is_(None),
                                          Post.author_id == author_id,))
    
    # 审核员审核帖子
    def _review_query(self):
        """
        审核相关查询：
        - 只过滤软删除, 发布状态
        - 不过滤审核状态（PENDING/APPROVED/REJECTED 都查得到）
        """
        return (self.db.query(Post).filter(Post.deleted_at.is_(None),
                Post.publish_status == PostPublishStatus.PUBLISHED.value,))

    # ---------- 创建 ----------

    def create_post(self, data: PostOnlyCreate) -> str:
        """
        只创建 posts 表记录：
        - 不处理内容表和统计表
        - 返回新帖子的 pid
        """
        payload = data.model_dump(exclude_none=True)
        post = Post(**payload)

        with transaction(self.db):
            self.db.add(post)

        # 刷新以获取 pid
        self.db.refresh(post)
        return post.pid

    
    # ---------- 用户功能：帖子查询，帖子更新，帖子软删除 ----------

    # 通过帖子id查看帖子，通常是检索查看，所以使用的是访客查询_viewer_query方法
    def viewer_get_post_by_pid(self, pid: str) -> Optional[PostOut]:
        """
        带内容 & 统计的帖子详情：
        - 通过 relationship 拿 PostContent / PostStats
        - 这里假定每个帖子都已经有对应的内容和统计记录
          如果可能为空，可以改成 Optional 字段并做判空处理
        """
        post: Post = (
            self._viewer_query()
            .filter(Post.pid == pid)
            .first()
        )
        if not post:
            return None

        return PostOut.model_validate(post)
    
    # 用户通过帖子id查看帖子, 使用作者查询_author_query方法
    def author_get_post_by_pid(self, pid: str, author_id: str) -> Optional[PostOut]:
        """
        带内容 & 统计的帖子详情：
        - 通过 relationship 拿 PostContent / PostStats
        - 这里假定每个帖子都已经有对应的内容和统计记录
          如果可能为空，可以改成 Optional 字段并做判空处理
        """
        post: Post = (
            self._author_query(author_id)
            .filter(Post.pid == pid)
            .first()
        )
        if not post:
            return None

        return PostOut.model_validate(post)

    # 在首页推荐出现的帖子，是访客查询
    def get_batch_posts(self, page: int, page_size: int) -> BatchPostsOut:
        """
        分页获取帖子列表：
        - 当前实现：按 _id 倒序（你也可以改成 created_at）
        - 通过 relationship 访问内容和统计（会触发懒加载）
          如果后面有性能问题，可以再加 joinedload 优化
        """
        base_q = self._viewer_query().order_by(Post._id.desc())

        total = base_q.count()
        posts: List[Post] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items: List[PostOut] = []
        items = [PostOut.model_validate(post) for post in posts]

        return BatchPostsOut(
            total=total,
            count=len(items),
            items=items,
        )
    
    # 通过作者id查看帖子，需要编写两种接口，一种是作者本人查询，一种是访客查询
    def get_posts_by_author(self, data: PostGet, page: int, page_size: int,) -> BatchPostsOut:
        # 作者本人访问自己的帖子
        if data.current_user_id == data.author_id:
            base_q = (self._author_query(data.author_id)
                      .order_by(Post._id.desc()))
        else:
            # 访客访问作者的公开帖子
            base_q = (
                self._viewer_query()
                .filter(Post.author_id == data.author_id)
                .order_by(Post._id.desc())
            )

        total = base_q.count()

        posts = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        items = [PostOut.model_validate(post) for post in posts]

        return BatchPostsOut(total=total, count=len(items), items=items)

    def update_post(self, pid: str, data: PostUpdate) -> bool:
        """
        更新帖子的可见性 / 发布状态
        - 业务规则（比如草稿 -> 发布的方向限制）建议放在业务层
        """
        post: Optional[Post] = (
            self.db.query(Post)
            .filter(Post.pid == pid)
            .first()
        )
        
        if not post:
            return False

        # 获取更新的数据
        update_data = data.model_dump(exclude_none=True)

        # 业务逻辑：如果发布状态为已发布 (1)，不允许变更为草稿 (0)
        if 'publish_status' in update_data and post.publish_status == 1:
            raise ForbiddenAction()
        
        # 更新数据
        with transaction(self.db):
            for field, value in update_data.items():
                setattr(post, field, value)

        return True

    # 用户软删除帖子
    def soft_delete_post(self, pid: str) -> bool:
        """
        软删除：打 deleted_at 时间戳
        """
        post: Optional[Post] = (
            self.db.query(Post)
            .filter((Post.pid == pid), Post.deleted_at.is_(None))
            .first()
        )
        if not post:
            return False

        with transaction(self.db):
            post.deleted_at = datetime.now(CN_TZ)

        return True
    
    
    # ---------- 审核员功能：查询帖子审核状态，更新审核状态（审核） ----------
    # 通过帖子id查看帖子审核状态
    def get_post_review_by_pid(self, pid: str) -> Optional[PostReviewOut]:
        """
        查询帖子审核信息（附带内容）：
        - 用于审核列表 / 审核详情展示
        """
        post: Post = (self._review_query().filter(Post.pid == pid).first())
        if not post:
            return None
        
        return PostReviewOut.model_validate(post)
    
    # 审核员通过用户id的帖子审核状态
    def get_post_reviews_by_author(self, author_id: str, page: int, page_size: int,) -> BatchPostsReviewOut:
        """
        通过作者 ID 查看该作者的所有帖子（包含所有审核状态）：
        - 过滤 deleted_at
        - 不过滤 review_status
        - 按 _id 倒序（可改为按创建时间）
        """
        base_q = (
            self._review_query()
            .filter(Post.author_id == author_id)
            .order_by(Post._id.desc())
        )
        total = base_q.count()
        posts: List[Post] = (
            base_q
            .offset(page * page_size)   # page 从 0 开始
            .limit(page_size)
            .all()
        )

        items: List[PostReviewOut] = []
        items = [PostReviewOut.model_validate(post) for post in posts]

        return BatchPostsReviewOut(total=total, count=len(items), items=items,)
    
    # 查看所有待审核帖子
    def list_pending_review_posts(self, page: int, page_size: int,) -> BatchPostsReviewOut:
        """
        查看所有待审帖子（管理员用）：
        - 只查 review_status = PENDING
        - 过滤 deleted_at
        """
        base_q = (
            self._review_query()
            .filter(Post.review_status == PostReviewStatus.PENDING.value)
            .order_by(Post._id.desc())
        )
        total = base_q.count()
        posts: List[Post] = (
            base_q
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        items: List[PostReviewOut] = []
        items = [PostReviewOut.model_validate(post) for post in posts]

        return BatchPostsReviewOut(total=total, count=len(items), items=items,)

    # 审核帖子
    def update_review(self, pid: str, data: PostReviewUpdate) -> bool:
        """
        更新审核状态 / 审核时间
        - 审核流程本身的业务约束建议在业务层控制
        """
        post: Optional[Post] = (
            self._review_query()
            .filter(Post.pid == pid)
            .first()
        )
        if not post:
            return False

        with transaction(self.db):
            post.review_status = data.review_status
            # 如果调用方没传 reviewed_at，则默认当前东八区时间
            if data.reviewed_at is not None:
                post.reviewed_at = data.reviewed_at
            else:
                post.reviewed_at = datetime.now(CN_TZ)

        return True
    

    # ---------- 管理员员功能：帖子查询（最高权限），帖子硬删除， ----------
    # 通过帖子id获取帖子信息
    def admin_get_post_by_pid(self, pid: str) -> Optional[PostAdminOut]:
        """
        管理员根据帖子 ID 获取帖子详情：
        - 不过滤 deleted_at（软删除也能看）
        """
        post: Optional[Post] = (
            self.db.query(Post)
            .filter(Post.pid == pid)
            .first()
        )
        if not post:
            return None

        return PostAdminOut.model_validate(post)

    # 查看所有帖子（含软删）
    def admin_list_all_posts(self, page: int, page_size: int) -> BatchPostsAdminOut:
        base_q = (
            self.db.query(Post)
            .order_by(Post._id.desc())
        )
        total = base_q.count()

        posts = (base_q.offset(page * page_size).limit(page_size).all())

        items: list[PostAdminOut] = []
        items = [PostAdminOut.model_validate(post) for post in posts]

        return BatchPostsAdminOut(total=total, count=len(items), items=items,)

    # 查看所有软删除帖子
    def admin_list_deleted_posts(self, page: int, page_size: int) -> BatchPostsAdminOut:
        base_q = (
            self.db.query(Post)
            .filter(Post.deleted_at.is_not(None))
            .order_by(Post._id.desc())
        )
        total = base_q.count()

        posts = (base_q.offset(page * page_size).limit(page_size).all())

        items: list[PostAdminOut] = []
        items = [PostAdminOut.model_validate(post) for post in posts]

        return BatchPostsAdminOut(total=total, count=len(items), items=items,)

    # 通过作者 ID 查看所有帖子（含软删）
    def admin_list_posts_by_author(self, author_id: str, page: int, page_size: int) -> BatchPostsAdminOut:
        base_q = (
            self.db.query(Post)
            .filter(Post.author_id == author_id)
            .order_by(Post._id.desc())
        )
        total = base_q.count()

        posts = (base_q.offset(page * page_size).limit(page_size).all())

        items: list[PostAdminOut] = []
        items = [PostAdminOut.model_validate(post) for post in posts]

        return BatchPostsAdminOut(total=total, count=len(items), items=items,)

    # 只有管理员才可以使用的帖子硬删除
    def hard_delete_post(self, pid: str) -> bool:
        """
        硬删除：直接从 posts 表删除
        - 注意：关联的内容 / 统计 / 评论等，
          推荐在业务层或外键级联 / relationship.cascade 中一并处理
        """
        # 包括已软删的帖子
        post: Optional[Post] = (
            self.db.query(Post)
            .filter(Post.pid == pid)
            .first()
        )
        if not post:
            return False

        with transaction(self.db):
            self.db.delete(post)

        return True

    def restore_post(self, pid: str) -> bool:
        """
        恢复帖子软删除：deleted_at → NULL
        """
        post = (
            self.db.query(Post)   # 管理员可见软删除
            .filter(Post.pid == pid)
            .first()
        )
        if not post:
            return False

        if post.deleted_at is None:
            return False

        with transaction(self.db):
            post.deleted_at = None

        return True