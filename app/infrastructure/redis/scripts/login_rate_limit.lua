local user_key = KEYS[1]
local ip_key = KEYS[2]

local now = tonumber(ARGV[1])

local user_window = tonumber(ARGV[2])
local user_limit = tonumber(ARGV[3])

local ip_window = tonumber(ARGV[4])
local ip_limit = tonumber(ARGV[5])

local request_id = ARGV[6]

-- Calculate window start
local user_window_start = now - user_window
local ip_window_start = now - ip_window

-- Remove expired attempts
redis.call(
    "ZREMRANGEBYSCORE",
    user_key,
    "-inf",
    user_window_start
)

redis.call(
    "ZREMRANGEBYSCORE",
    ip_key,
    "-inf",
    ip_window_start
)

-- Count current attempts
local user_count = redis.call(
    "ZCARD",
    user_key
)

local ip_count = redis.call(
    "ZCARD",
    ip_key
)

-- Check limits
if user_count >= user_limit then
    return {0, "user"}
end

if ip_count >= ip_limit then
    return {0, "ip"}
end

return {1, "allowed"}

-- -- Add current attempt
-- redis.call(
--     "ZADD",
--     user_key,
--     now,
--     request_id
-- )

-- redis.call(
--     "ZADD",
--     ip_key,
--     now,
--     request_id
-- )

-- return {1, "allowed"}