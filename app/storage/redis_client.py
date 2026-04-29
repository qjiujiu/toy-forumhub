import redis
from typing import Generator

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_DB = 0

# 建议开启 decode_responses=True，让 Redis 返回 str 而不是 bytes
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)

def get_redis() -> Generator[redis.Redis, None, None]:
    """
    FastAPI 依赖注入用的获取 redis 实例方法。
    这里直接复用全局 redis_client，连接本身是线程安全的。
    """
    try:
        yield redis_client
    finally:
        # 通常不需要关闭（连接池复用），这里留空即可
        pass