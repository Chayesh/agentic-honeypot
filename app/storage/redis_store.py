import json
import redis
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def get_redis_client():
    try:
        return redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True
        )
    except Exception as e:
        logger.error(f"Redis client init failed: {e}")
        return None

def get_state(conversation_id: str):
    client = get_redis_client()
    if not client:
        return None

    try:
        data = client.get(conversation_id)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Redis get failed: {e}")
        return None

def save_state(conversation_id: str, state: dict):
    client = get_redis_client()
    if not client:
        return

    try:
        client.set(conversation_id, json.dumps(state))
    except Exception as e:
        logger.error(f"Redis set failed: {e}")
