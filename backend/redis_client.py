import redis
import json
import os
import logging
from typing import Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("redis_client")

class RedisClient:
    _instance = None

    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.client = None
        self.connect()

    def connect(self):
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=2
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        except redis.ConnectionError:
            logger.warning(f"Could not connect to Redis at {self.redis_host}:{self.redis_port}. Caching disabled.")
            self.client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisClient()
        return cls._instance

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            val = self.client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.error(f"Redis get error key={key}: {e}")
            return None

    def set(self, key: str, value: Any, ex: int = 86400):
        """Set key with expiration (default 1 day)"""
        if not self.client:
            return
        try:
            self.client.set(key, json.dumps(value), ex=ex)
        except Exception as e:
            logger.error(f"Redis set error key={key}: {e}")

# Global instance
redis_client = RedisClient.get_instance()
