# ✅ Чек-лист готовності до деплою

## Передумови (Local)

- [ ] Python 3.11+ встановлений
- [ ] PostgreSQL або Docker встановлений
- [ ] Redis встановлений або Docker
- [ ] Git встановлений

## Крок 1: Локальне тестування

- [ ] Скопіював `.env.example` → `.env`
- [ ] Заповнив усі значення у `.env`:
  - [ ] `DJANGO_SECRET_KEY` (згенерував: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
  - [ ] `DATABASE_URL` (локально: `postgres://binify:binify@localhost:5432/binify`)
  - [ ] `REDIS_HOST=localhost`, `REDIS_PORT=6379`
  - [ ] `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (з Cloudflare R2)
  - [ ] `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`
- [ ] Запустив міграції: `python manage.py migrate`
- [ ] Запустив тести:
  - [ ] `python manage.py test bins`
  - [ ] `python manage.py test users`
- [ ] Локальний сервер працює: `python manage.py runserver`

## Крок 2: Docker локально (опціонально)

- [ ] Docker Desktop встановлений
- [ ] Запустив: `docker-compose build`
- [ ] Запустив: `docker-compose up -d`
- [ ] Перевірив статус: `docker-compose ps` (5 сервісів у стані Up)
- [ ] Запустив міграції: `docker-compose exec web python manage.py migrate`
- [ ] Перевірив доступність: http://localhost:8000

## Крок 3: Підготовка Production Сервісів

### База даних (Neon)

- [ ] Зареєструвався на [neon.tech](https://neon.tech)
- [ ] Створив проект `binify`
- [ ] Скопіював Connection String: `postgresql://user:password@host/neondb?sslmode=require`
- [ ] Перевірив з'єднання локально: `psql <CONNECTION_STRING>`

### Redis (Upstash)

- [ ] Зареєструвався на [upstash.com](https://upstash.com)
- [ ] Створив Redis базу `binify-redis`
- [ ] Скопіював:
  - [ ] `REDIS_HOST`
  - [ ] `REDIS_PORT`
  - [ ] `REDIS_PASSWORD`
- [ ] Перевірив підключення: `redis-cli -h <REDIS_HOST> -p <REDIS_PORT> -a <REDIS_PASSWORD> PING`

### R2 (Cloudflare)

- [ ] Зареєструвався на [Cloudflare](https://dash.cloudflare.com)
- [ ] Створив bucket `binify-content`
- [ ] Створив API token з правами Read/Write для бакету
- [ ] Скопіював:
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
  - [ ] `AWS_S3_ENDPOINT_URL` (з Bucket details)
  - [ ] `AWS_S3_CUSTOM_DOMAIN`

### Fly.io

- [ ] Зареєструвався на [fly.io](https://fly.io)
- [ ] Встановив Fly CLI: `curl -L https://fly.io/install.sh | sh` (macOS/Linux) або `choco install flyctl` (Windows)
- [ ] Авторизувався: `fly auth login`

## Крок 4: Деплой на Fly.io

- [ ] У папці проекту запустив: `fly launch`
- [ ] Вибрав назву приложення (наприклад, `binify-app`)
- [ ] Вибрав регіон (наприклад, `ams` — Amsterdam)
- [ ] **НЕ** деплоїв ще (відповів "No" на "Do you want to deploy?")
- [ ] Встановив усі секрети:
  ```bash
  fly secrets set DJANGO_SECRET_KEY="<згенерований-ключ>"
  fly secrets set DATABASE_URL="<neon-connection-string>"
  fly secrets set REDIS_HOST="<upstash-host>"
  fly secrets set REDIS_PORT="<upstash-port>"
  fly secrets set REDIS_PASSWORD="<upstash-password>"
  fly secrets set AWS_ACCESS_KEY_ID="<cloudflare-key>"
  fly secrets set AWS_SECRET_ACCESS_KEY="<cloudflare-secret>"
  fly secrets set AWS_STORAGE_BUCKET_NAME="binify-content"
  fly secrets set AWS_S3_ENDPOINT_URL="<r2-endpoint>"
  fly secrets set AWS_S3_CUSTOM_DOMAIN="<r2-domain>"
  fly secrets set ALLOWED_HOSTS="binify-app.fly.dev"
  fly secrets set CSRF_TRUSTED_ORIGINS="https://binify-app.fly.dev"
  ```
- [ ] Перевірив: `fly secrets list`
- [ ] Запустив деплой: `fly deploy`

## Крок 5: Production перевірка

- [ ] Відкрив сайт: `fly open`
- [ ] Перевірив логи: `fly logs -f`
- [ ] Перевірив, що немає 500 помилок
- [ ] Залогінився в SSH: `fly ssh console`
- [ ] У SSH запустив:
  ```bash
  python manage.py createsuperuser
  ```
- [ ] Перевірив admin панель: `https://binify-app.fly.dev/admin`
- [ ] Перевірив API endpoints:
  - [ ] `GET /api/bins/` — список бінів
  - [ ] `POST /api/bins/` — створення біна (з токеном JWT)

## Крок 6: Моніторинг

- [ ] Налаштував алерти у Fly.io dashboard
- [ ] Перевірив метрики: `fly status`
- [ ] Перевірив автомасштабування: `fly scale show`

## Крок 7 (Опціонально): CI/CD

- [ ] Створив GitHub repo
- [ ] Запушив код: `git push origin main`
- [ ] Налаштував Fly GitHub integration: `fly github-setup`
- [ ] Перевірив автоматичний деплой при `git push`

---

## 🎉 Готово!

Якщо всі пункти відмічені — твій Binify працює у production! 🚀

**Корисні команди після деплою:**
- Перегляд логів: `fly logs -f`
- SSH у сервер: `fly ssh console`
- Масштабування: `fly scale count 2` (2 інстанси)
- Оновлення: `fly deploy` (після `git push`)
- Видалення: `fly apps destroy binify-app`

**Якщо щось не працює:**
1. Перевір логи: `fly logs -f`
2. Перевір секрети: `fly secrets list`
3. Перевір статус: `fly status`
4. Див. [DEPLOY.md](DEPLOY.md) розділ "Моніторинг та налагодження"
