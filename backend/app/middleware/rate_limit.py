import time

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

# Redis client for rate limiting
_redis: redis.Redis | None = None


async def get_rate_limit_redis() -> redis.Redis:
    """Get or create Redis connection for rate limiting."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis sliding window rate limiter.
    Limits requests per IP to RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW seconds.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check
        if request.url.path == "/api/health":
            return await call_next(request)

        # Use client IP as the rate limit key
        client_ip = request.client.host if request.client else "unknown"
        key = f"paytrack:ratelimit:{client_ip}"

        try:
            r = await get_rate_limit_redis()
            current = await r.get(key)

            if current and int(current) >= settings.RATE_LIMIT_REQUESTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Try again later.",
                )

            pipe = r.pipeline()
            await pipe.incr(key)
            await pipe.expire(key, settings.RATE_LIMIT_WINDOW)
            await pipe.execute()

        except HTTPException:
            raise
        except Exception:
            # If Redis is down, allow the request through
            pass

        response = await call_next(request)
        return response
