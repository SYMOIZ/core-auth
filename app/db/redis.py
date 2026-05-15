from collections.abc import AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    global redis_client
    if redis_client is None:
        await init_redis()
    yield redis_client


async def blacklist_token(token: str, expires_in_seconds: int) -> None:
    global redis_client
    if redis_client is None:
        await init_redis()
    await redis_client.setex(f"blacklist:{token}", expires_in_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    global redis_client
    if redis_client is None:
        await init_redis()
    result = await redis_client.get(f"blacklist:{token}")
    return result is not None
