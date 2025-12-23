# Детальне керівництво деплою для Binify 🚀

Це керівництво описує, як завантажити твій Django сервер на **Fly.io** безкоштовно для початківців.

## Зміст
1. [Встановлення необхідних інструментів](#встановлення)
2. [Підготовка бази даних та Redis](#підготовка-сервісів)
3. [Налаштування секретів](#налаштування-секретів)
4. [Деплой на Fly.io](#деплой-на-flyio)
5. [Моніторинг та налагодження](#моніторинг)

---

## Встановлення

### 1. Fly CLI (Flyctl) — інструмент для деплою

#### На Windows
```powershell
# Установи через Chocolatey (якщо у тебе є Chocolatey)
choco install flyctl

# Або завантаж окремо з https://github.com/superfly/flyctl/releases
# Витягни ZIP та додай папку до PATH
```

#### На macOS/Linux
```bash
curl -L https://fly.io/install.sh | sh
```

### 2. Перевір, що Fly CLI встановлена
```bash
fly version  # Має вивести версію (наприклад, 0.1.85)
```

### 3. Зареєструйся на Fly.io
```bash
fly auth signup
# або якщо уже маєш аккаунт:
fly auth login
```

---

## Підготовка сервісів

### Крок 1: Бази даних PostgreSQL (Neon)

**Чому Neon?** Безкоштовний тарифний план, достатньо для розробки, легко інтегрується.

1. Перейди на [neon.tech](https://neon.tech)
2. Натисни "Sign Up" та зареєструйся через GitHub або email
3. Після реєстрації у консолі:
   - У лівій панелі клікни **"New Project"**
   - Назва проекту: `binify`
   - Database name: залишити за замовчуванням `neondb`
   - Натисни **"Create Project"**
4. Коли проект створений, побачиш **Connection String**:
   ```
   postgresql://user:password@host/dbname?sslmode=require
   ```
5. **Збережи цей рядок** — потрібен для fly.io

### Крок 2: Redis (Upstash)

**Чому Upstash?** Redis як сервіс без місцевої інфраструктури.

1. Перейди на [upstash.com](https://upstash.com)
2. Клікни **"Sign up"** (через GitHub найпростіше)
3. У консолі:
   - Клікни **"Create Database"**
   - Назва: `binify-redis`
   - Тип: Redis
   - Регіон: обрай поближче (наприклад, Frankfurt якщо в Європі)
   - Натисни **"Create"**
4. Коли Redis створено, у вкладці **"Details"** знайди:
   - **UPSTASH_REDIS_REST_URL** — REST endpoint (потім не знадобиться)
   - **Command Details** — видиме:
     ```
     REDIS_HOST: xxxxxx.upstash.io
     REDIS_PASSWORD: xxxxx
     REDIS_PORT: 39xxx (звичайно 39019)
     ```
5. **Збережи ці значення**

### Крок 3: Cloudflare R2 (сховище файлів)

**Чому R2?** Дешево для файлів, S3-сумісний API.

1. Перейди на [dashboard.cloudflare.com](https://dashboard.cloudflare.com)
2. У лівій панелі клікни **"R2"** → **"Create bucket"**
3. Назва бакету: `binify-content` (мала літера, без спеціальних символів)
4. Регіон: обрай автоматичний або поближче до тебе
5. Натисни **"Create bucket"**
6. Перейди на **Account Settings** → **R2 API tokens** → **Create API token**
   - Дай permissive permissions або обмежу на конкретний bucket
   - Натисни **"Create API Token"**
7. Збережи:
   - **Access Key ID**
   - **Secret Access Key**
8. Базовий URL бакету видно в Bucket details:
   ```
   https://xxxx.r2.cloudflarestorage.com
   ```

---

## Налаштування секретів

### Крок 1: Підготуй локально

Перед деплоєм перевір, що всі змінні встановлені. Скопіюй `.env.example` в `.env`:

```bash
cp .env.example .env
```

Відкрий `.env` та заповни:
```env
# Django
DEBUG=False
DJANGO_SECRET_KEY=твій-дуже-довгий-рандомний-ключ-мінімум-50-символів
SECRET_KEY_LENGTH=50

# База даних
DATABASE_URL=postgresql://user:password@host/neondb?sslmode=require

# Redis
REDIS_HOST=xxxxx.upstash.io
REDIS_PORT=39019
REDIS_PASSWORD=xxxxx-password
REDIS_DB=0

# R2 (Cloudflare)
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_STORAGE_BUCKET_NAME=binify-content
AWS_S3_REGION_NAME=auto
AWS_S3_CUSTOM_DOMAIN=xxxx.r2.cloudflarestorage.com

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CSRF/CORS
ALLOWED_HOSTS=binify-app.fly.dev,твій-домен.com
CSRF_TRUSTED_ORIGINS=https://binify-app.fly.dev,https://твій-домен.com

# Email (опціонально)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Крок 2: Перевір локальне тестування

Перед деплоєм, тесту локально:

```bash
# Міграції бази
python manage.py migrate

# Запус тестів
python manage.py test bins users

# Запус локального сервера
python manage.py runserver
```

Якщо все працює локально — готово до деплою!

### Крок 3: Встанови секрети на Fly.io

Коли готово, установи всі секретні змінні на Fly (Fly.io не відправляє `.env` автоматично):

```bash
# Перевір, чи знаходишся в папці проекту
cd c:\pythonfiles\firstprogect\app

# Встанови кожний секрет (замініть значення)
fly secrets set DJANGO_SECRET_KEY="твій-дуже-довгий-ключ"
fly secrets set DATABASE_URL="postgresql://user:password@host/neondb?sslmode=require"
fly secrets set REDIS_HOST="xxxxx.upstash.io"
fly secrets set REDIS_PORT="39019"
fly secrets set REDIS_PASSWORD="xxxxx"
fly secrets set AWS_ACCESS_KEY_ID="xxxxx"
fly secrets set AWS_SECRET_ACCESS_KEY="xxxxx"
fly secrets set AWS_STORAGE_BUCKET_NAME="binify-content"
fly secrets set AWS_S3_CUSTOM_DOMAIN="xxxx.r2.cloudflarestorage.com"
fly secrets set ALLOWED_HOSTS="binify-app.fly.dev"
fly secrets set CSRF_TRUSTED_ORIGINS="https://binify-app.fly.dev"

# Перевір, що все встановлено
fly secrets list
```

---

## Деплой на Fly.io

### Крок 1: Створи Fly приложення

```bash
# Переди в папку проекту
cd c:\pythonfiles\firstprogect\app

# Ініціалізуй Fly app
fly launch

# Це запитає:
# - Would you like to copy its configuration to the new app? → Yes
# - Do you want to tweak these settings before proceeding? → No
# - Do you want to deploy? → No (спочатку хочемо встановити секрети)
```

### Крок 2: Встанови базу та міграції

Коли Fly app створений, запусти міграції на production базі:

```bash
# Запусти міграції на production базі
fly ssh console

# У консолі (на сервері Fly) виконай:
cd /app
python manage.py migrate

# Вихід з консолі: Ctrl+D
```

### Крок 3: Запусти деплой

```bash
fly deploy
```

Чекай, поки образ Docker будує та завантажується. Це може зайняти 2-5 хвилин.

Коли завершить, побачиш:
```
==> Monitoring Deployment
```

### Крок 4: Перевір, що працює

```bash
# Отримай URL твого сайту
fly open

# Або вручну (замінь "binify-app" на своє ім'я)
https://binify-app.fly.dev
```

Якщо видиш **500 error** — см. розділ "Моніторинг".

---

## Моніторинг та налагодження

### Перегляд логів

```bash
# Живі логи
fly logs -f

# Логи за останні 24 години
fly logs --lines 100
```

### Частих помилок

#### 1. **500 Internal Server Error**
Скоріш за все, `DJANGO_SECRET_KEY` або database connection невірна.
```bash
# Перевір секрети
fly secrets list

# Перевір логи
fly logs -f
```

#### 2. **"ALLOWED_HOSTS" Error**
```
DisallowedHost: Invalid HTTP_HOST header: 'binify-app.fly.dev'
```
Встанови правильний ALLOWED_HOSTS:
```bash
fly secrets set ALLOWED_HOSTS="binify-app.fly.dev"
fly deploy
```

#### 3. **Database Connection Error**
Перевір `DATABASE_URL`:
```bash
fly ssh console
python -c "import os; print(os.getenv('DATABASE_URL'))"
```

#### 4. **Redis Connection Error**
Перевір `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`:
```bash
fly ssh console
python -c "import redis; r = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), password=os.getenv('REDIS_PASSWORD')); print(r.ping())"
```

### Масштабування

```bash
# Додай ще CPU/RAM до інстансу
fly scale vm performance-2x

# Запусти кілька інстансів для завантаженості
fly scale count 3
```

---

## Альтернативні платформи

### Koyeb (середня складність)
1. https://koyeb.com → Sign Up
2. Прив'яжи GitHub → выбери цей repo → Deploy
3. Встанови env vars у web UI
4. Deploy готовий через 5 хвилин

### Railway.app (легко)
1. https://railway.app → Deploy
2. Налаштуй env vars
3. Deploy

### Heroku (з коштами)
Heroku більше не безкоштовна, але була популярна. Пропускаємо.

---

## Дальше: Користувальницький домен

Коли app готова:
1. Зареєструй домен на Route53, Namecheap, або GoDaddy
2. На Fly:
   ```bash
   fly certs create твій-домен.com
   ```
3. Додай DNS записи у реєстраторі домену, як скажуть Fly
4. Оновім `ALLOWED_HOSTS` та `CSRF_TRUSTED_ORIGINS` на fly.io

---

## Залагодження: Git + CI/CD (бонус)

Щоб автоматично деплоїти на кожний `git push`:

1. У папці проекту ініціалізуй Git:
```bash
git init
git add .
git commit -m "Initial commit: Binify Django app"
```

2. На GitHub создай новий repo

3. Натисни `fly deploy --generate-github-deploy-token` або вручну:
```bash
fly github-setup
```

4. Тепер кожний раз, коли pushиш до main — Fly автоматично деплоїть!

---

## Шпаргалка команд

```bash
# Запуск
fly deploy

# Логи
fly logs -f

# SSH у сервер
fly ssh console

# Встановлення секретів
fly secrets set KEY="value"
fly secrets list

# Масштабування
fly scale count 3
fly scale vm performance-2x

# Видалення app
fly apps destroy binify-app
```

---

**Готово!** 🎉 Твої Bins тепер доступні в інтернеті!

Якщо щось не працює — перевір логи за допомогою `fly logs -f`. Більша частина помилок виявляється в перших 10 рядках логів.

