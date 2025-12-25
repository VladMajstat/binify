Hash generator service

This folder contains a small FastAPI service (`hash_service.py`) that fills `my_unique_hash_pool` in Redis/Upstash.

Quick deploy steps (local):
- Build and run with Docker:
  docker build -t binify-hash-generator .
  docker run -e UPSTASH_REDIS_REST_URL=... -e UPSTASH_REDIS_REST_TOKEN=... -p 8081:8081 binify-hash-generator

Fly deploy (recommended):
1. Create app:
   fly apps create binify-hash-generator --org personal --region ams
2. Set secrets (use your Upstash values):
   fly secrets set UPSTASH_REDIS_REST_URL="https://..." UPSTASH_REDIS_REST_TOKEN="..." --app binify-hash-generator
3. Deploy from this folder:
   cd hash_generator
   fly deploy --app binify-hash-generator

After deploy, verify logs and that `my_unique_hash_pool` is being rpush'ed.
