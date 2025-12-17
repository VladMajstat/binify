import boto3
import uuid
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
import redis
import json
from rapidfuzz import fuzz
from django.core.paginator import Paginator

from .models import Create_Bins


def get_redis_client():
    """Повертає Redis клієнт з налаштувань Django."""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
    )


def create_bin_from_data(request, data):
    try:
        filename = f"bins/bin_{uuid.uuid4().hex}.txt"
        file_url = upload_to_r2(filename, data["content"])
        expiry_at = get_expiry_map(data["expiry"])
        file_key = filename
        size_bin = get_bin_size(file_key)

        bin_obj = Create_Bins.objects.create(
            file_url=file_url,
            file_key=file_key,
            category=data["category"],
            language=data["language"],
            expiry=data["expiry"],
            expiry_at=expiry_at,
            access=data["access"],
            title=f"{request.user.username}/{data['title']}",
            tags=data["tags"],
            author=request.user,
            size_bin=size_bin,
        )

        redis_client = get_redis_client()

        # Отримуємо хеш напряму з Redis
        hash_value = redis_client.lpop("my_unique_hash_pool")

        if hash_value:
            hash_value_str = hash_value.decode("utf-8")
            try:
                # ...логіка створення біна з hash_value_str...
                bin_obj.hash = hash_value_str
                bin_obj.save(update_fields=["hash"])
            except Exception as e:
                # Якщо сталася помилка — повертаємо хеш назад у пул
                redis_client.lpush("my_unique_hash_pool", hash_value)
                print("Помилка при створенні біна:", e)
                return False
        else:
            print("Хеш не отримано з Redis!")
            return False

        return True
    except Exception as e:
        print(f"Помилка при створенні bin: {e}")
        return False

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        region_name=settings.AWS_S3_REGION_NAME,
    )

# Завантажує контент у Cloudflare R2 і повертає URL до файлу
def upload_to_r2(filename, content):
    # Підключення до R2 через boto3
    s3 = get_s3_client()

    # Завантаження файлу у бакет R2
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=filename,
        Body=content,
        ContentType="text/plain",
    )

    # Формуємо URL для доступу до файлу
    file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{filename}"
    
    return file_url

# Визначає дату видалення Bin залежно від вибраного терміну життя
def get_expiry_map(expiry):
    EXPIRY_MAP = {
        "never": None,
        "1m": timedelta(minutes=1),
        "1h": timedelta(hours=1),
        "12h": timedelta(hours=12),
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
        "2w": timedelta(weeks=2),
        "30d": timedelta(days=30),
        "6mo": timedelta(days=30 * 6),
        "1y": timedelta(days=365),
    }

    expiry_at = None
    # Якщо expiry не 'never', рахуємо дату видалення
    if expiry in EXPIRY_MAP and EXPIRY_MAP[expiry]:
        expiry_at = timezone.now() + EXPIRY_MAP[expiry]

    return expiry_at

def get_bin_content(bin_or_file_key, default="Контент не знайдено."):
    """
    Повертає контент біна з R2.
    Приймає або об'єкт біна (з file_key), або сам file_key.
    """
    if hasattr(bin_or_file_key, "file_key"):
        file_key = bin_or_file_key.file_key
        file_url = getattr(bin_or_file_key, "file_url", None)
        if not file_url:
            return default
    else:
        file_key = bin_or_file_key

    try:
        s3 = get_s3_client()
        obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return obj["Body"].read().decode("utf-8")
    except Exception as e:
        print(f"Не вдалося отримати контент з R2: {e}")
        return default

    # Повертає розмір файлу (біна) у байтах з Cloudflare R2 за file_key.
def get_bin_size(file_key):

    s3 = get_s3_client()
    try:
        obj = s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return obj['ContentLength']
    except Exception as e:
        print(f"Не вдалося отримати розмір з R2: {e}")
        return None


def delete_from_r2(file_key):
    """
    Видаляє файл з Cloudflare R2 за ключем file_key.
    """
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return True
    except Exception as e:
        print(f"Помилка при видаленні з R2: {e}")
        return False

def smart_search(query):
    """
    Розумний пошук по назві та мові.
    Повертає список Bin-ів, у яких схожість з запитом > 0.
    """
    if not query:
        return Create_Bins.objects.none()

    query = query.lower().strip()
    bins = Create_Bins.objects.all()
    results = []

    for bin in bins:
        # Порівнюємо з назвою
        title_score = fuzz.partial_ratio(query, bin.title.lower())
        # Порівнюємо з мовою (display)
        lang_score = fuzz.partial_ratio(query, bin.get_language_display().lower())
        # Якщо хоча б одна схожість > 50, додаємо у результати
        if max(title_score, lang_score) > 50:
            results.append((max(title_score, lang_score), bin))

    # Сортуємо за схожістю (від більшої до меншої)
    results.sort(reverse=True, key=lambda x: x[0])

    # Повертаємо тільки Bin-об'єкти
    bins_ids = [bin.id for score, bin in results]
    return Create_Bins.objects.filter(id__in=bins_ids).order_by("-created_at")


def cache_bin_meta_and_content(bin, bin_content=None, ttl_meta=3600, ttl_content=3600):
    """
    Кешує метадані та контент біна у Redis.
    """
    redis_cache = get_redis_client()
    meta_key = f"bin_meta:{bin.hash}"
    content_key = f"bin_content:{bin.hash}"

    meta = {
        "title": bin.title,
        "author": bin.author.username,
        "created_at": str(bin.created_at),
        "size_bin": getattr(bin, "size_bin", 0),
        "language": bin.language,
        "language_display": bin.get_language_display() if hasattr(bin, "get_language_display") else bin.language,
        "category": bin.category,
        "category_display": bin.get_category_display() if hasattr(bin, "get_category_display") else bin.category,
        "tags": getattr(bin, "tags", ""),
    }
    redis_cache.setex(meta_key, ttl_meta, json.dumps(meta))

    if bin_content is not None:
        redis_cache.setex(content_key, ttl_content, bin_content)


def invalidate_bin_cache(hash):
    """
    Видаляє кеш метаданих і контенту біна з Redis.
    """
    redis_cache = get_redis_client()
    meta_key = f"bin_meta:{hash}"
    content_key = f"bin_content:{hash}"
    redis_cache.delete(meta_key)
    redis_cache.delete(content_key)
