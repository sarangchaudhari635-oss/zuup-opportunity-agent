"""
Rate Limiting Middleware — Redis sliding window counter.
Authenticated users: 100 req/min. Unauthenticated: 10 req/min.
"""
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis import get_sync_redis

EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)

        # Determine if authenticated
        auth_header = request.headers.get("Authorization", "")
        is_authenticated = auth_header.startswith("Bearer ")

        # Choose limit
        limit = (
            settings.rate_limit_authenticated
            if is_authenticated
            else settings.rate_limit_unauthenticated
        )
        window = settings.rate_limit_window_seconds

        # Build key: use token prefix for auth, IP for unauth
        if is_authenticated:
            token_prefix = auth_header.split(" ")[1][:16]  # First 16 chars of token
            key = f"rate:auth:{token_prefix}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate:unauth:{client_ip}"

        # Sliding window counter in Redis
        try:
            redis = get_sync_redis()
            now = int(time.time())
            window_key = f"{key}:{now // window}"

            pipe = redis.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, window * 2)
            results = pipe.execute()
            count = results[0]

            if count > limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Max {limit} requests per {window} seconds.",
                        "code": "rate_limit_exceeded",
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(window),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
            return response

        except Exception:
            # If Redis is down, fail open (don't block requests)
            return await call_next(request)
