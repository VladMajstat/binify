# Швидкі команди для Binify

## Локальний розвиток

### Початкове налаштування
```bash
# Клонуй репозиторій
git clone <your-repo-url>
cd app

# Створи віртуальне середовище
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Встанови залежності
pip install -r requirements.txt

# Налаштуй .env
cp .env.example .env
# Відредагуй .env — заповни DATABASE_URL, REDIS_HOST, R2 credentials
```

### Запуск локально (без Docker)
```bash
# Запусти Redis (якщо є Docker)
docker run -d -p 6379:6379 redis:7

# Або установи Redis локально:
# Windows: choco install redis
# macOS: brew install redis && brew services start redis
# Linux: sudo apt install redis-server && sudo service redis-server start

# Запусти PostgreSQL (якщо є Docker)
docker run -d -p 5432:5432 -e POSTGRES_USER=binify -e POSTGRES_PASSWORD=binify -e POSTGRES_DB=binify postgres:15

# Або локально: https://www.postgresql.org/download/

# Міграції
python manage.py migrate

# Створи superuser
python manage.py createsuperuser

# Запусти сервер
python manage.py runserver

# У окремому терміналі: запусти воркер
python manage.py process_tasks

# Опціонально: hash service (у окремому терміналі)
uvicorn hash_generator.hash_service:app --reload --port 8001
```

### Тести
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

## Docker Compose

### Запуск
```bash
# Перевір .env
cp .env.example .env

# Збери образи
docker-compose build

# Запусти всі сервіси (PostgreSQL + Redis + Django + Worker + Hash Service)
docker-compose up -d

# Перевір статус
docker-compose ps

# Міграції
docker-compose exec web python manage.py migrate

# Створи superuser
docker-compose exec web python manage.py createsuperuser

# Перегляд логів
docker-compose logs -f
docker-compose logs -f web  # тільки Django
```

### Зупинка
```bash
# Зупинити
docker-compose down

# Зупинити + видалити volumes (УВАГА: видалить базу!)
docker-compose down -v
```

---

## Production (Fly.io)

### Перший деплой
```bash
# Встанови Fly CLI
# macOS/Linux: curl -L https://fly.io/install.sh | sh
# Windows: choco install flyctl

# Логін
fly auth login

# Створи app
fly launch
# Обери назву (наприклад, "my-binify")
# Обери регіон (наприклад, "ams" для Amsterdam)
# Відповів "No" на "Do you want to deploy?" (спочатку налаштуємо секрети)

# Встанови секрети (ОБОВ'ЯЗКОВО!)
fly secrets set DJANGO_SECRET_KEY="<згенеруй: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'>"
fly secrets set DATABASE_URL="<Neon PostgreSQL URL>"
fly secrets set REDIS_HOST="<Upstash host>"
fly secrets set REDIS_PORT="<Upstash port>"
fly secrets set REDIS_PASSWORD="<Upstash password>"
fly secrets set AWS_ACCESS_KEY_ID="<Cloudflare R2>"
fly secrets set AWS_SECRET_ACCESS_KEY="<Cloudflare R2>"
fly secrets set AWS_STORAGE_BUCKET_NAME="binify-content"
fly secrets set AWS_S3_ENDPOINT_URL="<R2 endpoint>"
fly secrets set AWS_S3_CUSTOM_DOMAIN="<R2 domain>"
fly secrets set ALLOWED_HOSTS="my-binify.fly.dev"
fly secrets set CSRF_TRUSTED_ORIGINS="https://my-binify.fly.dev"

# Перевір
fly secrets list

# Деплой
fly deploy

# Відкрий у браузері
fly open
```

### Оновлення коду
```bash
# Після змін у коді:
git add .
git commit -m "Update: опис змін"
fly deploy

# Або через GitHub Actions (якщо налаштовано)
git push origin main
```

### Моніторинг
```bash
# Логи
fly logs -f

# Статус
fly status

# SSH у контейнер
fly ssh console

# Перезапуск
fly apps restart my-binify

# Масштабування (більше CPU/RAM)
fly scale vm performance-2x

# Додати інстанси
fly scale count 2
```

### Міграції на production
```bash
# SSH у контейнер
fly ssh console

# Запусти міграції
python manage.py migrate

# Або створи superuser
python manage.py createsuperuser
```

---

## Корисні ресурси

### Документація
- [DEPLOY.md](DEPLOY.md) — детальний посібник деплою
- [DOCKER.md](DOCKER.md) — запуск через Docker Compose
- [CHECKLIST.md](CHECKLIST.md) — чек-лист перед деплоєм
- [README.md](README.md) — API документація та Ops guide

### Зовнішні сервіси
- **Neon** (PostgreSQL): https://neon.tech
- **Upstash** (Redis): https://upstash.com
- **Cloudflare R2**: https://dash.cloudflare.com/r2
- **Fly.io**: https://fly.io

### Команди Django
```bash
# Створи міграції
python manage.py makemigrations

# Застосуй міграції
python manage.py migrate

# Створи superuser
python manage.py createsuperuser

# Збір статики
python manage.py collectstatic

# Django shell
python manage.py shell

# Тестові дані
python manage.py create_test_bins

# Очищення прострочених bins
python manage.py delete_bins
```

---

## Налагодження

### Помилка: "Connection refused" до PostgreSQL
```bash
# Перевір, чи запущений PostgreSQL
# Docker: docker ps | grep postgres
# Локально: sudo service postgresql status

# Перевір DATABASE_URL у .env
echo $DATABASE_URL
```

### Помилка: "Redis connection error"
```bash
# Перевір, чи запущений Redis
docker ps | grep redis
# Локально: redis-cli ping

# Перевір REDIS_HOST у .env
```

### Помилка: "500 Internal Server Error" на Fly.io
```bash
# Перевір логи
fly logs -f

# Перевір секрети
fly secrets list

# Перевір статус
fly status

# SSH і перевір Django shell
fly ssh console
python manage.py shell
```

### Помилка: "ALLOWED_HOSTS" на production
```bash
# Встанови ALLOWED_HOSTS через fly secrets
fly secrets set ALLOWED_HOSTS="my-binify.fly.dev"
fly deploy
```

---

**Готово!** Обирай команди залежно від того, чим працюєш (локально, Docker, або production). 🚀
