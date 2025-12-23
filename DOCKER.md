# Локальний запуск через Docker Compose

Цей файл пояснює, як запустити весь проект локально за допомогою Docker Compose.

## Передумови

1. **Docker Desktop** встановлений ([завантажити](https://www.docker.com/products/docker-desktop/))
2. **Git** (для клонування репозиторію)

## Швидкий старт

### Крок 1: Підготовка середовища

```bash
# Скопіюй .env.example в .env
cp .env.example .env

# Відредагуй .env — встанови значення для локальної розробки
# Для Docker Compose використовуй ці налаштування:
DEBUG=True
DJANGO_SECRET_KEY=local-dev-key-not-for-production
DATABASE_URL=postgres://binify:binify@db:5432/binify
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# R2 (Cloudflare) — заповни реальними значеннями або залиш тестові
AWS_ACCESS_KEY_ID=твій-ключ
AWS_SECRET_ACCESS_KEY=твій-секрет
AWS_STORAGE_BUCKET_NAME=binify-bucket
AWS_S3_ENDPOINT_URL=https://xxxx.r2.cloudflarestorage.com
```

### Крок 2: Запуск усіх сервісів

```bash
# Збери образи
docker-compose build

# Запусти контейнери в фоні
docker-compose up -d

# Перевір, чи все працює
docker-compose ps
```

Маєш побачити 5 сервісів у стані **Up**:
- `app-db-1` (PostgreSQL)
- `app-redis-1` (Redis)
- `app-web-1` (Django)
- `app-hash-service-1` (FastAPI)
- `app-worker-1` (Background tasks)

### Крок 3: Запусти міграції

```bash
# Зайди всередину Django контейнера
docker-compose exec web bash

# Запусти міграції
python manage.py migrate

# Створи суперюзера (опціонально)
python manage.py createsuperuser

# Вихід з контейнера
exit
```

### Крок 4: Відкрий у браузері

Перейди на:
- **Django**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Hash Service (FastAPI)**: http://localhost:8001

### Крок 5: Перевірка логів

```bash
# Логи всіх сервісів
docker-compose logs -f

# Логи тільки Django
docker-compose logs -f web

# Логи тільки worker
docker-compose logs -f worker
```

---

## Корисні команди

### Запуск тестів

```bash
# Тести bins
docker-compose exec web python manage.py test bins

# Тести users
docker-compose exec web python manage.py test users

# Всі тести
docker-compose exec web python manage.py test
```

### Створення тестових даних

```bash
docker-compose exec web python manage.py create_test_bins
```

### Оновлення залежностей

```bash
# Встанови нові пакети у requirements.txt
docker-compose exec web pip install <package>

# Або перебудуй образи
docker-compose build --no-cache
docker-compose up -d
```

### Очищення

```bash
# Зупинити контейнери
docker-compose down

# Видалити контейнери та volumes (УВАГА: видалить базу даних!)
docker-compose down -v

# Видалити образи
docker-compose down --rmi all
```

---

## Налагодження

### Проблема: "Connection refused" до PostgreSQL

**Рішення**: Перевір, чи контейнер `db` запущений:
```bash
docker-compose ps db
docker-compose logs db
```

### Проблема: "Redis connection error"

**Рішення**: Перевір, чи `redis` доступний:
```bash
docker-compose exec redis redis-cli ping
# Має відповісти: PONG
```

### Проблема: Django не запускається

**Рішення**: Перевір логи:
```bash
docker-compose logs web
```

Можливі причини:
- Не встановлені міграції → `docker-compose exec web python manage.py migrate`
- Неправильні env vars → перевір `.env`

### Проблема: Порт вже зайнятий

Якщо `8000` або `5432` зайняті іншими програмами:

```yaml
# У docker-compose.yml змени порти
services:
  web:
    ports:
      - "9000:8000"  # зовнішній порт 9000, внутрішній 8000
```

---

## Структура Docker Compose

```
┌─────────────────┐
│   PostgreSQL    │ (db)
│   Port: 5432    │
└────────┬────────┘
         │
┌────────▼────────┐
│     Redis       │ (redis)
│   Port: 6379    │
└────────┬────────┘
         │
    ┌────▼─────┬───────────┬────────────┐
    │          │           │            │
┌───▼───┐  ┌──▼───┐  ┌────▼──────┐  ┌──▼──────┐
│ Django│  │Worker│  │Hash Service│  │ Volume  │
│  web  │  │tasks │  │  FastAPI   │  │ static  │
│ :8000 │  │      │  │   :8001    │  │ media   │
└───────┘  └──────┘  └────────────┘  └─────────┘
```

---

## Production vs Local

| Налаштування | Local (Docker Compose) | Production (Fly.io) |
|--------------|------------------------|---------------------|
| DEBUG | True | False |
| DATABASE_URL | `db:5432` | Neon PostgreSQL |
| REDIS_HOST | `redis` | Upstash |
| ALLOWED_HOSTS | `*` | `твій-домен.fly.dev` |
| SECURE_SSL_REDIRECT | False | True |

---

**Готово!** Тепер можеш працювати з Binify локально через Docker Compose. 🐳

Для деплою на production див. [DEPLOY.md](DEPLOY.md).
