import time
import uuid
from pathlib import Path

from app.infrastructure.redis.client import redis_client


USER_LIMIT = 5
USER_WINDOW = 2 * 60

IP_LIMIT = 20
IP_WINDOW = 60


LUA_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "infrastructure"
    / "redis"
    / "scripts"
    / "login_rate_limit.lua"
)

with open(LUA_SCRIPT_PATH, "r") as file:
    LOGIN_RATE_LIMIT_SCRIPT = file.read()

async def check_login_rate_limit(
    user_id: int,
    ip_address: str,
):
    user_key = f"login:rate:user:{user_id}"
    ip_key = f"login:rate:ip:{ip_address}"

    now = int(time.time() * 1000)
    request_id = str(uuid.uuid4())

    user_window_ms = USER_WINDOW * 1000
    ip_window_ms = IP_WINDOW * 1000


    result = await redis_client.eval(
        LOGIN_RATE_LIMIT_SCRIPT,
        2,
        user_key,
        ip_key,
        now,
        user_window_ms,
        USER_LIMIT,
        ip_window_ms,
        IP_LIMIT,
        request_id,
    )

    allowed = result[0] == 1
    reason = result[1]

    return {
        "allowed": allowed,
        "reason": reason,
    }

async def check_ip_rate_limit(ip_address: str):
    key = f"login:rate:ip:{ip_address}"

    now = int(time.time() * 1000)
    window_start = now - (IP_WINDOW * 1000)

    await redis_client.zremrangebyscore(
        key,
        "-inf",
        window_start,
    )

    count = await redis_client.zcard(key)

    if count >= IP_LIMIT:
        return {
            "allowed": False,
            "reason": "ip",
        }

    return {
        "allowed": True,
        "reason": "allowed",
    }


async def record_failed_login(
    user_id: int | None,
    ip_address: str,
):
    ip_key = f"login:rate:ip:{ip_address}"

    now = int(time.time() * 1000)

    request_id = str(uuid.uuid4())

    await redis_client.zadd(
        ip_key,
        {
            request_id: now,
        },
    )

    if user_id is not None:
        user_key = f"login:rate:user:{user_id}"

        await redis_client.zadd(
            user_key,
            {
                request_id: now,
            },
        )







    