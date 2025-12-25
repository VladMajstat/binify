FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY .. /app

# Install only required packages for the hash service
RUN pip install --no-cache-dir upstash-redis fastapi uvicorn

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8081/get_hash/ || exit 1

CMD ["uvicorn", "hash_generator.hash_service:app", "--host", "0.0.0.0", "--port", "8081"]
