import json              # Converts Python objects to JSON and vice versa.
import hashlib           # Used to generate unique cache keys.
import logging           # Records warnings/errors in log files.

from functools import wraps

from flask import current_app, request

# Handles Redis connection errors.
from redis.exceptions import RedisError

# Redis client stored in extensions.py
from app import extensions

# Logger object
log = logging.getLogger(__name__)


# CREATE UNIQUE CACHE KEY

# Every cached response needs a unique key.
# Example URL:
# /treks?difficulty=Easy&page=2
#
# Instead of storing the full URL, it is converted into an MD5 hash.

#Why use MD5?
# MD5 creates a fixed-length unique identifier that is shorter and easier to use as a Redis key.

def _make_key(prefix: str, *parts) -> str:

    # Join all parts into one string.
    raw = ":".join(str(p) for p in parts)

    # Generate unique cache key.
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"


# GET DATA FROM CACHE
# Checks whether requested data already exists in Redis.
#
# If found:
#     Return cached data.
#
# Otherwise:
#     Return None.
#
def cache_get(key: str):

    # Redis client object.
    client = extensions.redis_client

    # Redis not initialized.
    if client is None:
        return None

    try:
        # Fetch value from Redis.
        val = client.get(key)

    except RedisError as e:

        # Redis server unavailable.
        # Application continues normally.
        log.warning(
            "Redis GET failed (%s) — serving without cache",
            e
        )
        return None

    # Redis stores strings.
    # Convert JSON back into Python object.
    return json.loads(val) if val else None


# SAVE DATA INTO CACHE
# Stores API response into Redis.

# TTL = Time To Live
# After TTL expires,
# Redis automatically deletes the cache.
#
def cache_set(key: str, value, ttl: int = None):

    client = extensions.redis_client

    if client is None:
        return

    # Use configured TTL.
    # till when the data should be cached.
    ttl = ttl or current_app.config.get("TREK_CACHE_TTL", 60)

    try:

        # setex()
        # Set value with expiration time.
        client.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )

    except RedisError as e:

        log.warning(
            "Redis SETEX failed (%s) — response not cached",
            e
        )


# DELETE CACHE
# Removes all cached trek data.

# Example:
# After creating/updating/deleting a trek.
# Otherwise users may receive outdated information.
#
def cache_delete_prefix(prefix: str):

    client = extensions.redis_client

    if client is None:
        return

    try:

        # Scan every cache key beginning with prefix.
        for key in client.scan_iter(f"{prefix}:*"):

            # Delete cache.
            client.delete(key)

    except RedisError as e:

        log.warning(
            "Redis invalidation failed (%s)",
            e
        )


# CACHE DECORATOR

# This decorator automatically caches trek listing responses.

# Example:
#
# @cached_treks_response
# def get_all_treks():
#
# First request:
# Database queried.

# Second request:
# Data returned directly from Redis.
# Much faster.

def cached_treks_response(view_fn):

    @wraps(view_fn)

    def wrapper(*args, **kwargs):

        # Generate cache key using complete URL.
        cache_key = _make_key(
            "treks",
            request.full_path
        )

        # Check Redis first.
        cached = cache_get(cache_key)

        # Cache hit.
        if cached is not None:
            return cached

        # Cache miss.
        # Execute original function.
        result = view_fn(*args, **kwargs)

        # Cache only JSON serializable responses.
        if isinstance(result, (dict, list)):
            cache_set(cache_key, result)

        return result

    return wrapper