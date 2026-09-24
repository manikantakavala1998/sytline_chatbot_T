"""
Dynamic Permission Resolver (master prompt section 19) — decides ALLOW or
DENY for an operation (READ / EXECUTE / INSERT / UPDATE / DELETE) against
a resource, based on the current user's groups.

The permission DATA below (MOCK_GROUP_PERMISSIONS) is mocked — real group
permissions come from SyteLine once section 73's questions are answered.
The RESOLVING LOGIC here is real: group lookup, Redis short-lived caching
(section 19's "permission changes must not require AI retraining" — or,
right now, an app restart), and fail-open-on-cache-unavailable so a Redis
hiccup degrades to "just resolve fresh" rather than breaking every
request. Swapping the mock table for a real SyteLine permission lookup
later does not change any of this file's public functions or callers.
"""

from dataclasses import dataclass

import redis

from backend.app.config import settings
from backend.app.integrations.syteline.session_context import SyteLineUser
from backend.app.utils.logger import get_logger, log_event

CACHE_TTL_SECONDS = 30

logger = get_logger(__name__)

# group -> set of (operation, resource) pairs it's allowed to perform.
# "NO_ACCESS" is deliberately empty, so the Context Simulator can
# demonstrate a real DENY, not just always-allow like the Phase 1 seam.
MOCK_GROUP_PERMISSIONS: dict[str, set[tuple[str, str]]] = {
    "SALES_REP": {("READ", "assistant"), ("READ", "qa"), ("READ", "markdown_rag")},
    "AR_CLERK": {("READ", "assistant"), ("READ", "qa"), ("READ", "markdown_rag")},
    "NO_ACCESS": set(),
}


@dataclass
class PermissionDecision:
    allowed: bool
    reason: str


_redis_client: redis.Redis | None = None
_redis_unavailable = False


def _get_redis() -> redis.Redis | None:
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.redis_host, port=settings.redis_port, db=settings.redis_db, socket_connect_timeout=1
        )
    return _redis_client


def _mock_lookup(user: SyteLineUser, operation: str, resource: str) -> bool:
    return any((operation, resource) in MOCK_GROUP_PERMISSIONS.get(group, set()) for group in user.groups)


def resolve_permission(
    user: SyteLineUser,
    operation: str,
    resource: str,
    request_id: str | None = None,
) -> PermissionDecision:
    cache_key = f"perm:{user.user_id}:{operation}:{resource}"

    client = _get_redis()
    if client is not None:
        try:
            cached = client.get(cache_key)
            if cached is not None:
                allowed = cached == b"1"
                log_event(
                    logger,
                    "permission_cache_hit",
                    request_id=request_id,
                    user_id=user.user_id,
                    operation=operation,
                    resource=resource,
                    allowed=allowed,
                )
                return PermissionDecision(allowed=allowed, reason="cached")
        except redis.RedisError:
            global _redis_unavailable
            _redis_unavailable = True
            logger.warning(
                "event=permission_cache_unavailable request_id=%s action=resolve_fresh",
                request_id,
            )
            client = None

    allowed = _mock_lookup(user, operation, resource)

    if client is not None:
        try:
            client.setex(cache_key, CACHE_TTL_SECONDS, "1" if allowed else "0")
        except redis.RedisError:
            logger.warning(
                "event=permission_cache_write_failed request_id=%s action=continue_without_cache",
                request_id,
            )

    log_event(
        logger,
        "permission_resolved",
        request_id=request_id,
        user_id=user.user_id,
        operation=operation,
        resource=resource,
        allowed=allowed,
    )
    return PermissionDecision(allowed=allowed, reason="resolved" if allowed else "denied")
