import redis
import os
from dotenv import load_dotenv
import json
from pydantic import BaseModel

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def cache_template(template_id: str, template_data):
    # If it's a Pydantic model, use .json(); otherwise, dump normally
    if isinstance(template_data, BaseModel):
        data_str = template_data.json()
    else:
        data_str = json.dumps(template_data, default=str)

    redis_client.set(f"template:{template_id}", data_str)

def get_cached_template(template_id: str, model_class=None):
    cached = redis_client.get(f"template:{template_id}")
    if not cached:
        return None
    data = json.loads(cached)
    return model_class(**data) if model_class else data

def invalidate_cache(template_id: str):
    redis_client.delete(f"template:{template_id}")
