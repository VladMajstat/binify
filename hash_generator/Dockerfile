FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the hash_generator package and related files from this folder
# using the current build context. This ensures `hash_generator` is at /app/hash_generator
## Copy package files into /app/hash_generator so `import hash_generator` works
COPY . /app/hash_generator

# Normalize possible nested copy scenarios:
# - If build context was repo root, files may have been copied as /app/hash_generator/hash_generator
#   Move nested folder to /app/hash_generator so `import hash_generator` finds the package.
RUN if [ -d /app/hash_generator/hash_generator ]; then \
            mv /app/hash_generator/hash_generator /tmp/_hg && rm -rf /app/hash_generator && mv /tmp/_hg /app/hash_generator; \
        fi

# Install only required packages for the hash service
RUN pip install --no-cache-dir upstash-redis fastapi uvicorn requests redis

# Ensure Python will look in common locations for the package (covers different build contexts)
ENV PYTHONPATH=/app:/app/hash_generator:/app/hash_generator/hash_generator

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8081/get_hash/ || exit 1

# Use JSON CMD to run the start launcher (avoids shell quoting issues)
CMD ["python", "-u", "/app/hash_generator/start.py"]
