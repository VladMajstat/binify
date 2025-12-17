"""
Сервісний шар для роботи з бінами (business logic).
Тут — функції для створення та оновлення bin, які використовують
утиліти (`upload_to_r2`, `get_bin_size`, `delete_from_r2`, `get_expiry_map`).

Мета: винести важку логіку з view/serializer у окреме місце, щоб її
легко тестувати й повторно використовувати.
"""
from django.db import transaction
from django.core.exceptions import ValidationError

import redis
import uuid

from .utils import (
    upload_to_r2,
    get_bin_size,
    delete_from_r2,
    get_expiry_map,
    get_bin_content,
    invalidate_bin_cache,
    get_redis_client,
)
from .models import Create_Bins


class ServiceError(Exception):
    """Власний тип помилок сервісного шару."""
    pass


def create_bin_service(user, data):
    """Створює bin: завантажує content у R2, створює запис у БД, прив'язує hash з Redis."""

    content = data.get("content", "") or ""
    if not content.strip():
        raise ValidationError("Content cannot be empty")

    # Генеруємо ключ для файлу
    file_key = f"bins/bin_{uuid.uuid4().hex}.txt"

    # 1) Завантаження у R2
    try:
        file_url = upload_to_r2(file_key, content)
    except Exception as e:
        raise ServiceError(f"Upload to R2 failed: {e}")

    # 2) Отримуємо розмір (ContentLength) — fallback на довжину контенту
    try:
        size = get_bin_size(file_key)
        if size is None:
            size = len(content.encode("utf-8"))
    except Exception:
        size = len(content.encode("utf-8"))

    # 3) Підготовка інших полів
    title = f"{user.username}/{data.get('title','')}"
    expiry = data.get("expiry", "never")
    expiry_at = get_expiry_map(expiry)

    # 4) Створюємо запис у БД у транзакції
    try:
        with transaction.atomic():
            bin_obj = Create_Bins.objects.create(
                file_url=file_url,
                file_key=file_key,
                category=data.get("category", "NONE"),
                language=data.get("language", "none"),
                expiry=expiry,
                expiry_at=expiry_at,
                access=data.get("access", "public"),
                title=title,
                tags=data.get("tags", ""),
                author=user,
                size_bin=size,
            )

            # Робота з Redis: беремо hash з пулу
            try:
                redis_client = get_redis_client()
                hash_value = redis_client.lpop("my_unique_hash_pool")
                if hash_value:
                    hash_value_str = hash_value.decode("utf-8")
                    bin_obj.hash = hash_value_str
                    bin_obj.save(update_fields=["hash"])  # зберігаємо тільки hash
                else:
                    # Немає хеша в пулі — це критична ситуація для вашого flow
                    raise ServiceError("No hash available in pool")
            except Exception as exc:
                # Якщо робота з Redis впала — завертаємо причину в ServiceError, щоб API повернуло коректний код
                raise ServiceError(f"Redis error: {exc}")

            return bin_obj

    except Exception as e:
        # У випадку помилки після upload — намагаємось видалити файл з R2
        try:
            delete_from_r2(file_key)
        except Exception:
            pass
        # Перепакуємо помилку у ServiceError, якщо це не ValidationError
        if isinstance(e, (ValidationError, ServiceError)):
            raise
        raise ServiceError(f"Failed to create bin: {e}")


def update_bin_service(bin_obj, user, data):
    """Оновлює bin: перезаписує файл у R2 (за тим же file_key) і оновлює метадані."""

    # Перевірка прав: лише автор може оновлювати
    if bin_obj.author != user:
        raise ServiceError("Permission denied: only author can update bin")

    # Якщо немає змін по content — оновлюємо лише мета
    content = data.get("content")

    # Почнемо транзакцію для оновлення метаданих
    try:
        with transaction.atomic():
            if content is not None:
                if not str(content).strip():
                    raise ValidationError("Content cannot be empty")

                # Використовуємо існуючий file_key (перезапис)
                file_key = bin_obj.file_key or f"bins/bin_{uuid.uuid4().hex}.txt"
                try:
                    file_url = upload_to_r2(file_key, content)
                except Exception as e:
                    raise ServiceError(f"Upload to R2 failed: {e}")

                # Оновлюємо поля біну
                bin_obj.file_key = file_key
                bin_obj.file_url = file_url
                try:
                    bin_obj.size_bin = get_bin_size(file_key) or len(str(content).encode("utf-8"))
                except Exception:
                    bin_obj.size_bin = len(str(content).encode("utf-8"))

            # Інші оновлювані поля (title, tags, expiry, access, language, category)
            title = data.get("title")
            if title:
                bin_obj.title = f"{user.username}/{title}"

            for field in ("tags", "expiry", "access", "language", "category"):
                if field in data:
                    setattr(bin_obj, field, data.get(field))

            bin_obj.save()
            return bin_obj

    except Exception as e:
        # Якщо щось не так — не видаляємо файл тут, оскільки ми перезаписували існуючий
        if isinstance(e, (ValidationError, ServiceError)):
            raise
        raise ServiceError(f"Failed to update bin: {e}")


def get_bin_service(bin_obj, user):
    """Повертає метадані та контент біна (читання)."""

    content = get_bin_content(bin_obj, default=None)

    return {
        "id": bin_obj.pk,
        "hash": bin_obj.hash,
        "title": bin_obj.title,
        "language": bin_obj.language,
        "category": bin_obj.category,
        "access": bin_obj.access,
        "expiry": bin_obj.expiry,
        "expiry_at": bin_obj.expiry_at,
        "tags": bin_obj.tags,
        "size_bin": getattr(bin_obj, "size_bin", None),
        "file_url": bin_obj.file_url,
        "content": content,
    }


def delete_bin_service(bin_obj, user):
    """Видаляє bin: перевіряє права, видаляє з R2 та з БД, чистить кеш."""

    if bin_obj.author != user:
        raise ServiceError("Permission denied: only author can delete bin")

    file_key = bin_obj.file_key
    bin_hash = bin_obj.hash

    # Спершу намагаємось видалити з R2 (зовнішній ресурс)
    if file_key:
        deleted = delete_from_r2(file_key)
        if not deleted:
            raise ServiceError("Failed to delete file from R2")

    # Видаляємо запис у БД у транзакції
    try:
        with transaction.atomic():
            bin_obj.delete()
    except Exception as exc:
        raise ServiceError(f"Failed to delete bin: {exc}")

    # Чистимо кеш, якщо використовувався hash
    if bin_hash:
        try:
            invalidate_bin_cache(bin_hash)
        except Exception:
            pass

    return True
