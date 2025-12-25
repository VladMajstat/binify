from fastapi import FastAPI
import base64
import redis as redis_py
import threading
import os
import time
from upstash_redis import Redis as UpstashRedis

app = FastAPI()

# Instantiate redis client from env: prefer Upstash REST if provided, otherwise fall back to redis-py
try:
    if os.getenv("UPSTASH_REDIS_REST_URL") and os.getenv("UPSTASH_REDIS_REST_TOKEN"):
        redis_client = UpstashRedis(url=os.getenv("UPSTASH_REDIS_REST_URL"), token=os.getenv("UPSTASH_REDIS_REST_TOKEN"))
    else:
        redis_client = redis_py.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")), db=int(os.getenv("REDIS_DB", "0")), password=os.getenv("REDIS_PASSWORD") or None)
except Exception:
    redis_client = redis_py.Redis(host="localhost", port=6379)

POOL_KEY = "my_unique_hash_pool"
LAST_ID_KEY = "last_id"
HASH_SET_KEY = "hash_set"  # Для контролю унікальності

def generate_hash(id_num: int) -> str:
    b64 = base64.urlsafe_b64encode(id_num.to_bytes(6, "big")).decode("utf-8")
    return b64[:8]


def hash_producer():
    while True:
        last_id = int(redis_client.get(LAST_ID_KEY) or 1)
        # Генеруємо 10 хешів за раз, якщо пул менше 100
        if redis_client.llen(POOL_KEY) < 100:
            for i in range(10):
                hash_value = generate_hash(last_id + i)
                # Перевіряємо унікальність через Redis set
                if not redis_client.sismember(HASH_SET_KEY, hash_value):
                    redis_client.rpush(POOL_KEY, hash_value)
                    redis_client.sadd(HASH_SET_KEY, hash_value)
            redis_client.set(LAST_ID_KEY, last_id + 10)
        time.sleep(1)


threading.Thread(target=hash_producer, daemon=True).start()

@app.get("/get_hash/")
def get_hash():
    try:
        hash_value = redis_client.lpop(POOL_KEY)
        if hash_value:
            if isinstance(hash_value, (bytes, bytearray)):
                return {"hash": hash_value.decode("utf-8")}
            return {"hash": str(hash_value)}
    except Exception:
        return {"error": "Redis unavailable"}
    return {"error": "No hash available"}

# uvicorn hash_generator.hash_service:app --reload
# uvicorn hash_generator.hash_service:app --reload --port 8081
