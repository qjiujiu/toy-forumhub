from typing import Optional, Protocol

from app.schemas.v2.post_stats import PostStatsCreate, PostStatsOut, PostStatsDto, BatchPostStatsOut


class IPostStatsRepository(Protocol):

    def create(self, data: PostStatsCreate) -> str:
        pass

    def get_by_post_id(self, post_id: str) -> Optional[PostStatsOut]:
        pass

    def update(self, post_id: str, data: PostStatsDto, delta: int = 1) -> bool:
        pass

    def get_top_liked(self, limit: int = 10) -> BatchPostStatsOut:
        pass

    def get_top_commented(self, limit: int = 10) -> BatchPostStatsOut:
        pass

    def get_top_liked_with_posts(self, limit: int = 10) -> list:
        pass

    def get_top_commented_with_posts(self, limit: int = 10) -> list:
        pass