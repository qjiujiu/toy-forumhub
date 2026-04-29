from sqlalchemy.orm import Session
from typing import Optional
from app.models.v1.post_content import PostContent

from app.schemas.v2.post_content import PostContentCreate, PostContentUpdate, PostContentOut

from app.storage.v2.post_content.post_content_interface import IPostContentRepository

from app.core.db import transaction


class SQLAlchemyPostContentRepository(IPostContentRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PostContentCreate) -> str:
        post_content = PostContent(
            post_id=data.post_id,
            title=data.title,
            content=data.content,
        )
        with transaction(self.db):
            self.db.add(post_content)
        self.db.refresh(post_content)
        return post_content.pcid

    def get_by_post_id(self, post_id: str) -> Optional[PostContentOut]:
        post_content = (
            self.db.query(PostContent)
            .filter(PostContent.post_id == post_id)
            .first()
        )
        return PostContentOut.model_validate(post_content) if post_content else None

    def update(self, post_id: str, data: PostContentUpdate) -> bool:
        post_content = (
            self.db.query(PostContent)
            .filter(PostContent.post_id == post_id)
            .first()
        )
        if not post_content:
            return False
        update_data = data.model_dump(exclude_none=True)
        with transaction(self.db):
            for field, value in update_data.items():
                setattr(post_content, field, value)
        return True