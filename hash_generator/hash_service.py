from fastapi import FastAPI
import base64
import redis
import threading
import time


app = FastAPI()

redis_client = redis.Redis(host="localhost", port=6379)

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
    hash_value = r.lpop(POOL_KEY)
    if hash_value:
        return {"hash": hash_value.decode("utf-8")}
    return {"error": "No hash available"}

# uvicorn hash_generator.hash_service:app --reload
# uvicorn hash_generator.hash_service:app --reload --port 8001
