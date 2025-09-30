from fastapi import FastAPI
import base64

app = FastAPI()


def generate_hash(id_num: int) -> str:
    b64 = base64.urlsafe_b64encode(id_num.to_bytes(6, "big")).decode("utf-8")
    return b64[:8]


@app.get("/get_hash/")
def get_hash(id: int):
    hash_value = generate_hash(id)
    return {"hash": hash_value}

# uvicorn hash_generator.hash_service:app --reload
# uvicorn hash_generator.hash_service:app --reload --port 8001
