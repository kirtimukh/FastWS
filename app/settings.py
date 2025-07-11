import os
from dotenv import load_dotenv
import redis.asyncio


load_dotenv()

APP_ID = os.getenv("APP_ID", f"pid-{os.getpid()}")
REDIS_CHANNEL = "broadcast"

redis = redis.asyncio.from_url("redis://redis:6379", decode_responses=True, db=1)
