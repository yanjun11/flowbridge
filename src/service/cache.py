"""Redis 缓存工具"""
import redis.asyncio as redis
from src.conf import settings

_redis_client = None


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def check_and_set_processed(event_id: str, ttl: int = 3600) -> bool:
    """
    检查事件是否已处理，如果未处理则标记为已处理
    返回 True 表示是新事件，False 表示已处理过
    """
    client = await get_redis()
    key = f"flowbridge:event:{event_id}"
    result = await client.set(key, "1", ex=ttl, nx=True)
    return bool(result)
