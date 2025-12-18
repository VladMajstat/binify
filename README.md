# Ops Guide (non-API)

### Cloudflare R2 (boto3)
- Конфіг у [app/settings.py](app/settings.py#L64-L101): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN`, `AWS_S3_REGION_NAME`.
- Операції: завантаження, читання, видалення у [bins/utils.py](bins/utils.py#L20-L108) — функції `upload_to_r2`, `get_bin_content`, `get_bin_size`, `delete_from_r2`.

### Redis
- Конфіг: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` у [app/settings.py](app/settings.py#L157-L199).
- Використання: кеш метаданих/контенту (`bin_meta:<hash>`, `bin_content:<hash>`) та пул унікальних хешів `my_unique_hash_pool` у [bins/utils.py](bins/utils.py#L10-L68).
- Швидкий старт: `docker run -d -p 6379:6379 redis:7`.

### Hash generator service (FastAPI)
- Код: [hash_generator/hash_service.py](hash_generator/hash_service.py).
- Що робить: фоновий продюсер наповнює Redis-список `my_unique_hash_pool` унікальними 8-символьними хешами (контроль через Redis set для унікальності).
- Старт: після Redis запустити `uvicorn hash_generator.hash_service:app --reload --port 8081`.
- Споживання: `create_bin_from_data` у [bins/utils.py](bins/utils.py#L26-L67) бере хеш через `lpop`; якщо пул порожній — створення біна завершується невдачею.

### Background cleanup
- Завдання: `delete_expired_bins_task` у [bins/tasks.py](bins/tasks.py) видаляє прострочені біни й файли в R2.
- Запуск воркера: `python manage.py process_tasks` (django-background-tasks) у окремому процесі/сервісі.

### Management commands
- Тестові дані: [bins/management/commands/create_test_bins.py](bins/management/commands/create_test_bins.py).

### Local run order
1) Підняти Redis (наприклад, Docker: `docker run -d -p 6379:6379 redis:7`).
2) Запустити hash service: `uvicorn hash_generator.hash_service:app --reload --port 8081` (опціонально, якщо потрібен пул хешів).
3) Заповнити `.env` (R2 ключі) або оновити дефолти в [app/settings.py](app/settings.py#L64-L101).
4) Запустити Django: `python manage.py runserver`.
5) Запустити воркер очищення: `python manage.py process_tasks`.

---

# REST API (RU)

## Поток аутентификации
- Логин: `POST /api/token/` с `{ "username": "<user>", "password": "<pass>" }` → `access`, `refresh`.
- Использование: `Authorization: Bearer <access>` во всех защищённых запросах.
- Обновление: `POST /api/token/refresh/` с `{ "refresh": "<REFRESH>" }` → новый `access`.
- TTL: `access` ~30 мин, `refresh` ~30 дней (см. `SIMPLE_JWT` в [app/settings.py](app/settings.py#L103-L155)).
- Хранение: in-memory или `sessionStorage`; не класть в `localStorage`.

## Карта эндпойнтов
| Method | Path | Назначение | Auth |
| --- | --- | --- | --- |
| POST | /api/token/ | Получить `access`/`refresh` | Нет |
| POST | /api/token/refresh/ | Обновить `access` | Нет |
| POST | /bins/api/create/ | Создать бин | Да |
| GET | /bins/api/bin/<pk>/ | Получить бин по id | Нет (приватные → 403) |
| GET | /bins/api/bin/raw/<pk>/ | Raw по id (text/plain) | Нет (приватные → 403) |
| GET | /bins/api/bin/raw/hash/<hash>/ | Raw по hash | Нет (приватные → 403) |
| PUT | /bins/api/update/<pk>/ | Обновить бин (полный payload) | Да (author) |
| DELETE | /bins/api/delete/<pk>/ | Удалить бин | Да (author/staff) |
| POST | /bins/api/bulk-delete/ | Массовое удаление | Да |
| GET | /bins/api/bins/ | Список публичных (пагинация, фильтры) | Нет |
| GET | /bins/api/my-bins/ | Бины текущего пользователя | Да |
| GET | /bins/api/search/?q=... | Поиск бинов | Нет |
| GET | /bins/api/popular/ | Популярные бины | Нет |

## Примеры тел запросов
- Логин: `POST /api/token/`
  ```json
  { "username": "user", "password": "pass" }
  ```
- Рефреш: `POST /api/token/refresh/`
  ```json
  { "refresh": "<REFRESH>" }
  ```
- Создать бин: `POST /bins/api/create/` (auth)
  ```json
  {
    "content": "Hello",
    "title": "Sample",
    "language": "python",
    "expiry": "1d",
    "access": "public",
    "tags": "demo,example"
  }
  ```
- Обновить бин: `PUT /bins/api/update/123/` (auth)
  ```json
  {
    "content": "Updated",
    "title": "Sample",
    "language": "python",
    "expiry": "1d",
    "access": "public",
    "tags": "demo"
  }
  ```
- Массовое удаление: `POST /bins/api/bulk-delete/` (auth)
  ```json
  { "bin_ids": [1, 2, 3] }
  ```
- Прочие: `GET /bins/api/bin/123/`, `GET /bins/api/bin/raw/123/`, `GET /bins/api/bin/raw/hash/abcd123/`, `GET /bins/api/bins/?page=1&language=python&category=Software&author=john&active=true`, `GET /bins/api/my-bins/?active=true`, `GET /bins/api/search/?q=hello`, `GET /bins/api/popular/`.

## Postman helper (RU)
Test после `/api/token/`:
```javascript
const data = pm.response.json();
pm.environment.set("token", data.access);
console.log("New token saved:", data.access);
```

---

# REST API (EN)

## Auth flow
- Login: `POST /api/token/` with `{ "username": "<user>", "password": "<pass>" }` → `access`, `refresh`.
- Use: add `Authorization: Bearer <access>` to protected requests.
- Refresh: `POST /api/token/refresh/` with `{ "refresh": "<refresh>" }` → new `access`.
- TTL: `access` ~30 min, `refresh` ~30 days (see `SIMPLE_JWT` in [app/settings.py](app/settings.py#L103-L155)).
- Storage: in-memory or `sessionStorage`; avoid `localStorage`.

## Endpoint map
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| POST | /api/token/ | Obtain `access`/`refresh` | No |
| POST | /api/token/refresh/ | Refresh `access` | No |
| POST | /bins/api/create/ | Create bin | Yes |
| GET | /bins/api/bin/<pk>/ | Get bin by id | No (private → 403) |
| GET | /bins/api/bin/raw/<pk>/ | Raw content by id (text/plain) | No (private → 403) |
| GET | /bins/api/bin/raw/hash/<hash>/ | Raw content by hash | No (private → 403) |
| PUT | /bins/api/update/<pk>/ | Update bin (full payload) | Yes (author) |
| DELETE | /bins/api/delete/<pk>/ | Delete bin | Yes (author/staff) |
| POST | /bins/api/bulk-delete/ | Delete multiple bins | Yes |
| GET | /bins/api/bins/ | Public bins list (pagination, filters) | No |
| GET | /bins/api/my-bins/ | Current user's bins | Yes |
| GET | /bins/api/search/?q=... | Search bins | No |
| GET | /bins/api/popular/ | Popular bins | No |

## Request bodies (examples)
- Login: `POST /api/token/`
  ```json
  { "username": "user", "password": "pass" }
  ```
- Refresh: `POST /api/token/refresh/`
  ```json
  { "refresh": "<REFRESH>" }
  ```
- Create bin: `POST /bins/api/create/` (auth)
  ```json
  {
    "content": "Hello",
    "title": "Sample",
    "language": "python",
    "expiry": "1d",
    "access": "public",
    "tags": "demo,example"
  }
  ```
- Update bin: `PUT /bins/api/update/123/` (auth)
  ```json
  {
    "content": "Updated",
    "title": "Sample",
    "language": "python",
    "expiry": "1d",
    "access": "public",
    "tags": "demo"
  }
  ```
- Bulk delete: `POST /bins/api/bulk-delete/` (auth)
  ```json
  { "bin_ids": [1, 2, 3] }
  ```
- Others: `GET /bins/api/bin/123/`, `GET /bins/api/bin/raw/123/`, `GET /bins/api/bin/raw/hash/abcd123/`, `GET /bins/api/bins/?page=1&language=python&category=Software&author=john&active=true`, `GET /bins/api/my-bins/?active=true`, `GET /bins/api/search/?q=hello`, `GET /bins/api/popular/`.

## Postman helper (EN)
Test tab after `/api/token/`:
```javascript
const data = pm.response.json();
pm.environment.set("token", data.access);
console.log("New token saved:", data.access);
```

---

## Pagination and throttling
- Pagination: page-number style, 20 items per page by default (`?page=2`).
- Throttling: anon `100/day`, user `1000/day` (see `REST_FRAMEWORK` settings).

## Error hints
- 401: missing/expired access → refresh token or re-login.
- 403: authenticated but forbidden (permission denied).
- 400/422: validation errors; check field names and types.

## Notes
- CSRF applies to session-auth browser forms; JWT API requests do not require CSRF token.
- To force JWT-only on specific views, set `authentication_classes = [JWTAuthentication]` in those DRF views.
