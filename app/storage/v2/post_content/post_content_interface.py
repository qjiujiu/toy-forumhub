from typing import Optional, Protocol

from app.schemas.v2.post_content import PostContentCreate, PostContentUpdate, PostContentOut


class IPostContentRepository(Protocol):

    def create(self, data: PostContentCreate) -> str:
        pass

    def get_by_post_id(self, post_id: str) -> Optional[PostContentOut]:
        pass

    def update(self, post_id: str, data: PostContentUpdate) -> bool:
        pass