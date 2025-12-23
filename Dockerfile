# Multistage build для оптимізації розміру контейнера
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Встановлюємо залежності для компіляції
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо requirements і встановлюємо пакети
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Встановлюємо тільки runtime залежності
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо Python пакети, встановлені в builder у папку користувача
# pip з опцією --user встановлює пакети у /root/.local у builder, тому копіюємо звідти
COPY --from=builder /root/.local /root/.local

# Встановлюємо PATH і порт
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBUG=False \
    PORT=8000

# Копіюємо проект
COPY . .

# Збираємо статику (не залежить від бази даних)
RUN python manage.py collectstatic --noinput --clear || true

# Експортуємо порт
EXPOSE 8000

# Health check для Fly.io та Docker Compose
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Команда запуску: запускаємо Gunicorn, порт береться з `PORT` (без автоматичних міграцій)
# Міграції виконуються як `release_command` у fly.toml або вручну під час деплою
CMD ["sh", "-c", "gunicorn app.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-60} --access-logfile - --error-logfile -"]
