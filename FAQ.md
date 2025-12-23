# FAQ — Часті питання

## Загальні

### Q: Який стек технологій використовується?
**A:** 
- **Backend:** Django 5.2 + Django REST Framework
- **Auth:** JWT (SimpleJWT) + Session auth (hybrid)
- **Database:** PostgreSQL (production: Neon.tech)
- **Cache/Queue:** Redis (production: Upstash)
- **Storage:** Cloudflare R2 (S3-сумісний)
- **Hash Generator:** FastAPI + Redis pool
- **WSGI:** Gunicorn (production)
- **Static Files:** WhiteNoise

### Q: Чи безкоштовно деплоїти на Fly.io?
**A:** Так, Fly.io має free tier:
- 3 shared-cpu VMs (256MB RAM кожна)
- 160GB egress/місяць
- Persistent volumes (3GB)

Для production базових потреб (до ~1000 requests/день) — вистачить безкоштовного тарифу.

### Q: Скільки коштує використання Neon, Upstash, Cloudflare R2?
**A:**
- **Neon (PostgreSQL):** Free tier — 1 база, 500MB storage, 10 branches
- **Upstash (Redis):** Free tier — 10,000 requests/day, 256MB storage
- **Cloudflare R2:** Free tier — 10GB storage, 1M Class A requests/month

Для невеликих проектів — повністю безкоштовно.

---

## Локальний розвиток

### Q: Як запустити проект локально без Docker?
**A:**
```bash
# 1. Створи віртуальне середовище
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Встанови залежності
pip install -r requirements.txt

# 3. Налаштуй .env
cp .env.example .env
# Відредагуй .env: DATABASE_URL, REDIS_HOST, тощо

# 4. Запусти Redis локально
docker run -d -p 6379:6379 redis:7

# 5. Запусти PostgreSQL локально
docker run -d -p 5432:5432 -e POSTGRES_USER=binify -e POSTGRES_PASSWORD=binify -e POSTGRES_DB=binify postgres:15

# 6. Міграції
python manage.py migrate

# 7. Запусти сервер
python manage.py runserver
```

### Q: Як запустити проект локально через Docker Compose?
**A:**
```bash
# 1. Налаштуй .env
cp .env.example .env

# 2. Запусти всі сервіси (PostgreSQL, Redis, Django, Worker, Hash Service)
docker-compose up -d

# 3. Міграції
docker-compose exec web python manage.py migrate

# 4. Створи superuser
docker-compose exec web python manage.py createsuperuser

# 5. Відкрий http://localhost:8000
```

Детальний гід: [DOCKER.md](DOCKER.md)

### Q: Як запустити тести?
**A:**
```bash
# Усі тести
python manage.py test

# Тільки bins
python manage.py test bins

# Тільки users
python manage.py test users

# З деталями
python manage.py test --verbosity=2
```

---

## Docker

### Q: Як оновити залежності у Docker?
**A:**
```bash
# 1. Додай пакет у requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Перебудуй образ
docker-compose build web

# 3. Перезапусти контейнер
docker-compose up -d web
```

### Q: Як зайти всередину контейнера Django?
**A:**
```bash
docker-compose exec web bash

# Або для одноразової команди:
docker-compose exec web python manage.py shell
```

### Q: Як очистити volumes (база даних, Redis)?
**A:**
```bash
# УВАГА: Це видалить усі дані!
docker-compose down -v
```

### Q: Чому порт 8000 зайнятий?
**A:** Перевір, чи не запущений інший процес:
```bash
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000

# Змини порт у docker-compose.yml:
services:
  web:
    ports:
      - "9000:8000"  # Зовнішній 9000, внутрішній 8000
```

---

## Production (Fly.io)

### Q: Як деплоїти оновлення коду?
**A:**
```bash
# 1. Зміни код локально
git add .
git commit -m "Update: опис змін"

# 2. Деплой
fly deploy

# Або через GitHub Actions (якщо налаштовано)
git push origin main  # auto-deploy
```

### Q: Як переглянути логи на Fly.io?
**A:**
```bash
# Живі логи
fly logs -f

# Останні 100 рядків
fly logs --lines 100

# Логи за останню годину
fly logs --since 1h
```

### Q: Як зайти в SSH на Fly.io?
**A:**
```bash
fly ssh console

# У SSH можеш:
python manage.py shell
python manage.py migrate
python manage.py createsuperuser
```

### Q: Як оновити env vars (секрети)?
**A:**
```bash
# Додати/оновити секрет
fly secrets set NEW_VAR="value"

# Переглянути всі секрети (значення приховані)
fly secrets list

# Видалити секрет
fly secrets unset OLD_VAR
```

### Q: Як масштабувати app?
**A:**
```bash
# Більше інстансів (horizontal scaling)
fly scale count 3  # 3 VM instances

# Більше CPU/RAM (vertical scaling)
fly scale vm performance-2x

# Автоматичне масштабування (уже налаштовано у fly.toml)
# auto_start_machines = true
# auto_stop_machines = true
```

### Q: Що робити при помилці 500 Internal Server Error?
**A:**
```bash
# 1. Перевір логи
fly logs -f

# 2. Перевір секрети
fly secrets list

# 3. Зайди в SSH та перевір Django shell
fly ssh console
python manage.py shell

# 4. Перевір DATABASE_URL
python -c "import os; print(os.getenv('DATABASE_URL'))"

# 5. Перевір міграції
python manage.py showmigrations
```

### Q: Помилка "DisallowedHost: Invalid HTTP_HOST header"
**A:**
```bash
# Встанови правильний ALLOWED_HOSTS
fly secrets set ALLOWED_HOSTS="твій-домен.fly.dev"
fly deploy
```

---

## Database

### Q: Як підключитися до production бази (Neon)?
**A:**
```bash
# Використовуй connection string з Neon dashboard
psql "postgresql://user:password@host/neondb?sslmode=require"

# Або через pgAdmin, DBeaver з тим самим URL
```

### Q: Як зробити бекап бази даних?
**A:**
```bash
# Локально (Docker Compose)
docker-compose exec db pg_dump -U binify binify > backup.sql

# Production (Neon)
pg_dump "postgresql://user:password@host/neondb?sslmode=require" > backup.sql

# Відновлення
psql "postgresql://user:password@host/neondb?sslmode=require" < backup.sql
```

### Q: Як запустити міграції на production?
**A:**
```bash
fly ssh console
python manage.py migrate
```

---

## Redis

### Q: Як перевірити, чи працює Redis?
**A:**
```bash
# Локально (Docker)
docker-compose exec redis redis-cli ping
# Має відповісти: PONG

# Upstash (production)
redis-cli -h <REDIS_HOST> -p <REDIS_PORT> -a <REDIS_PASSWORD> ping
```

### Q: Як очистити кеш Redis?
**A:**
```bash
# Локально (Docker)
docker-compose exec redis redis-cli FLUSHDB

# Production (SSH на Fly)
fly ssh console
python manage.py shell

# У shell:
import redis
r = redis.Redis(host='<REDIS_HOST>', port=<REDIS_PORT>, password='<REDIS_PASSWORD>')
r.flushdb()
```

### Q: Як переглянути ключі у Redis?
**A:**
```bash
# Локально
docker-compose exec redis redis-cli KEYS "*"

# Production (у Django shell)
fly ssh console
python manage.py shell

# У shell:
import redis, os
r = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), password=os.getenv('REDIS_PASSWORD'))
print(r.keys('*'))
```

---

## Cloudflare R2

### Q: Як перевірити, чи працює R2?
**A:**
```bash
# У Django shell (локально або на Fly):
python manage.py shell

# У shell:
from bins.utils import upload_to_r2
url = upload_to_r2("test.txt", "Hello World!")
print(url)  # Має повернути URL
```

### Q: Як видалити файл з R2?
**A:**
```bash
# У Django shell:
from bins.utils import delete_from_r2
delete_from_r2("file_key_123")
```

### Q: Як переглянути всі файли у R2 bucket?
**A:**
Перейди на [Cloudflare dashboard](https://dash.cloudflare.com) → R2 → твій bucket → Files

---

## Hash Generator Service

### Q: Навіщо потрібен окремий hash service?
**A:** Генерує унікальні 8-символьні хеші заздалегідь та зберігає у Redis пулі. Django просто бере готовий хеш через `lpop`, замість того щоб перевіряти унікальність у базі кожного разу.

### Q: Як запустити hash service локально?
**A:**
```bash
# Після запуску Redis:
uvicorn hash_generator.hash_service:app --reload --port 8001

# Або через Docker Compose (автоматично):
docker-compose up -d hash-service
```

### Q: Що робити, якщо пул хешів порожній?
**A:** 
1. Перевір, чи запущений hash service
2. Почекай 5-10 секунд (сервіс наповнює пул у фоні)
3. Перевір Redis:
   ```bash
   docker-compose exec redis redis-cli LLEN my_unique_hash_pool
   ```

---

## Налагодження

### Q: "ModuleNotFoundError: No module named 'X'"
**A:**
```bash
# Перевір, чи встановлені залежності
pip install -r requirements.txt

# Або у Docker:
docker-compose build web
```

### Q: "django.db.utils.OperationalError: could not connect to server"
**A:**
1. Перевір, чи запущений PostgreSQL
2. Перевір DATABASE_URL у .env
3. Перевір, чи PostgreSQL слухає на правильному порті (5432)

### Q: "Connection refused" до Redis
**A:**
1. Перевір, чи запущений Redis: `docker ps | grep redis`
2. Перевір REDIS_HOST у .env (localhost або redis для Docker)
3. Перевір порт: 6379

### Q: "CSRF verification failed"
**A:**
1. Перевір CSRF_TRUSTED_ORIGINS у .env
2. Для API використовуй JWT Bearer токен (CSRF не потрібен)
3. Для форм додай `{% csrf_token %}` у template

---

## Безпека

### Q: Як згенерувати новий SECRET_KEY?
**A:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Q: Чи безпечно зберігати .env у Git?
**A:** **НІ!** `.env` має бути в `.gitignore`. Використовуй `.env.example` як шаблон, але **ніколи не коммить .env з реальними секретами**.

### Q: Як захистити API від brute-force атак?
**A:** Вже налаштовано у `settings.py`:
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
}
```

Можеш зменшити ліміти для більшої безпеки.

---

## Інше

### Q: Як додати кастомний домен до Fly.io?
**A:**
```bash
# 1. Додай сертифікат
fly certs create твій-домен.com

# 2. Оновіть DNS записи у реєстраторі домену (як скаже Fly)
# 3. Оновіть ALLOWED_HOSTS
fly secrets set ALLOWED_HOSTS="твій-домен.com,www.твій-домен.com"
fly secrets set CSRF_TRUSTED_ORIGINS="https://твій-домен.com,https://www.твій-домен.com"
```

### Q: Як видалити app з Fly.io?
**A:**
```bash
fly apps destroy твій-app-name
```

### Q: Чи можна використовувати SQLite замість PostgreSQL?
**A:** Локально — так, але **НЕ для production**. SQLite не підтримує concurrent writes, що критично для web-додатків.

---

**Не знайшов відповідь?**
- Перевір [DEPLOY.md](DEPLOY.md) для деплою
- Перевір [COMMANDS.md](COMMANDS.md) для швидких команд
- Перевір логи: `fly logs -f` (production) або `docker-compose logs -f` (локально)
