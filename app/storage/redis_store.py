import json
import redis
from app.config import settings

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

def get_state(conversation_id: str):
    data = redis_client.get(conversation_id)
    return json.loads(data) if data else None

def save_state(conversation_id: str, state: dict):
    redis_client.set(conversation_id, json.dumps(state))
