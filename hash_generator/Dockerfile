FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the hash_generator package and related files from this folder
# using the current build context. This ensures `hash_generator` is at /app/hash_generator
## Copy package files into /app/hash_generator so `import hash_generator` works
COPY . /app/hash_generator

# Install only required packages for the hash service
RUN pip install --no-cache-dir upstash-redis fastapi uvicorn requests redis

# Ensure Python will look in common locations for the package (covers different build contexts)
ENV PYTHONPATH=/app:/app/hash_generator:/app/hash_generator/hash_generator

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8081/get_hash/ || exit 1

CMD ["sh", "-c", "python -c \"import sys, importlib, os; print('PYTHONPATH:', sys.path); print('FIND_SPEC:', importlib.util.find_spec('hash_generator')); os.system('ls -la /app || true'); os.system('ls -la /app/hash_generator || true'); os.system('ls -la /app/hash_generator/hash_generator || true')\"; exec uvicorn hash_generator.hash_service:app --host 0.0.0.0 --port 8081]
