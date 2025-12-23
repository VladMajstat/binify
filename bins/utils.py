import boto3
import uuid
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
import redis
import json
import logging
import sys
from botocore.exceptions import ClientError
from rapidfuzz import fuzz
from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework import status

from .models import Create_Bins

logger = logging.getLogger(__name__)


def get_bin_or_error(**lookup):
    """
    Повертає бін за заданим lookup або Response з помилкою 404.
    
    Args:
        **lookup: Keyword arguments для пошуку біна (наприклад, pk=123, hash='abc')
    
    Returns:
        tuple: (bin_obj, None) якщо бін знайдено, або (None, error_response) якщо ні
    
    Examples:
        bin, error = get_bin_or_error(pk=123)
        bin, error = get_bin_or_error(hash='abc123')
    """
    try:
        return Create_Bins.objects.get(**lookup), None
    except Create_Bins.DoesNotExist:
        # Визначаємо назву поля і значення для повідомлення
        field, value = next(iter(lookup.items()))
        field_name = "id" if field == "pk" else field
        error_response = Response(
            {"detail": f"Bin with {field_name} '{value}' not found"},
            status=status.HTTP_404_NOT_FOUND
        )
        return None, error_response


def get_redis_client():
    """
    Повертає налаштований Redis клієнт з параметрів Django settings.
    
    Returns:
        redis.Redis: Підключений Redis клієнт
    """
    # Спробуємо підключитися до реального Redis; якщо не вдається — повертаємо локальний фейк.
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            socket_connect_timeout=1,
        )
        # Перевірка живучості — невеликий ping
        client.ping()
        return client
    except Exception as e:
        logger.warning("Redis unavailable (%s), falling back to in-memory FakeRedis", e)

        class FakeRedis:
            def __init__(self):
                self.store = {}
                self.lists = {}

            def setex(self, name, time, value):
                if isinstance(value, str):
                    value = value.encode("utf-8")
                self.store[name] = value

            def get(self, name):
                return self.store.get(name)

            def delete(self, *names):
                for n in names:
                    self.store.pop(n, None)

            def lpop(self, name):
                lst = self.lists.get(name, [])
                if lst:
                    return lst.pop(0)
                return None

            def lpush(self, name, value):
                lst = self.lists.setdefault(name, [])
                lst.insert(0, value)

            # Для сумісності з деякими викликами redis
            def ping(self):
                return True

        return FakeRedis()


def create_bin_from_data(request, data):
    """
    Створює новий бін з даних форми, завантажує контент у R2 та отримує унікальний хеш з Redis.
    
    Args:
        request: Django HTTP request об'єкт з авторизованим користувачем
        data (dict): Словник з даними біна (content, title, category, language, expiry, access, tags)
    
    Returns:
        bool: True якщо бін успішно створено, False у разі помилки
    
    Notes:
        - Завантажує контент у Cloudflare R2
        - Отримує унікальний хеш з Redis пулу my_unique_hash_pool
        - Повертає хеш назад у пул при помилці створення
    """
    try:
        filename = f"bins/bin_{uuid.uuid4().hex}.txt"
        # Обчислюємо розмір локально з вмісту — це працює у тестах, де upload_to_r2 може бути змокано
        # і уникатиме непотрібних запитів до R2 для файлів, які ще не існують.
        content_bytes = data.get("content", "").encode("utf-8")
        size_bin = len(content_bytes)

        file_url = upload_to_r2(filename, data["content"])
        expiry_at = get_expiry_map(data["expiry"])
        file_key = filename

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
            # Безпечне приведення значення хеша до str.
            # У тестах redis може бути мок (MagicMock), або lpop може повернути bytes.
            try:
                if isinstance(hash_value, (bytes, bytearray)):
                    hash_value_str = hash_value.decode("utf-8")
                else:
                    # Якщо є метод decode (наприклад, MagicMock), намагаймося викликати його,
                    # але захопимо помилки і врешті-решт приведемо до str().
                    try:
                        decoded = hash_value.decode("utf-8") if hasattr(hash_value, "decode") else None
                    except Exception:
                        decoded = None
                    hash_value_str = decoded if isinstance(decoded, str) else str(hash_value)
            except Exception:
                hash_value_str = str(hash_value)

            try:
                # ...логіка створення біна з hash_value_str...
                bin_obj.hash = hash_value_str
                bin_obj.save(update_fields=["hash"])
            except Exception as e:
                # Якщо сталася помилка — повертаємо хеш назад у пул (best-effort)
                try:
                    redis_client.lpush("my_unique_hash_pool", hash_value)
                except Exception:
                    pass
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
    """
    Створює та повертає налаштований boto3 S3 клієнт для роботи з Cloudflare R2.
    
    Returns:
        boto3.client: S3-сумісний клієнт для операцій з R2
    """
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        region_name=settings.AWS_S3_REGION_NAME,
    )

def upload_to_r2(filename, content):
    """
    Завантажує контент у Cloudflare R2 бакет і повертає публічний URL до файлу.
    
    Args:
        filename (str): Шлях до файлу в бакеті (ключ), наприклад 'bins/bin_abc123.txt'
        content (str): Текстовий контент для завантаження
    
    Returns:
        str: Публічний HTTPS URL до завантаженого файлу
    """
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

def get_expiry_map(expiry):
    """
    Визначає дату та час видалення біна залежно від вибраного терміну життя.
    
    Args:
        expiry (str): Термін дії ('never', '1m', '1h', '12h', '1d', '1w', '2w', '30d', '6mo', '1y')
    
    Returns:
        datetime or None: Час видалення або None якщо expiry='never'
    """
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
    Повертає текстовий контент біна з Cloudflare R2.
    
    Args:
        bin_or_file_key: Або об'єкт Create_Bins (з атрибутом file_key), або рядок file_key
        default (str): Значення за замовчуванням при помилці завантаження
    
    Returns:
        str: Текстовий контент біна або значення default
    """
    if hasattr(bin_or_file_key, "file_key"):
        file_key = bin_or_file_key.file_key
        file_url = getattr(bin_or_file_key, "file_url", None)
        if not file_url:
            return default
    else:
        file_key = bin_or_file_key

    # Якщо об'єкт відсутній — повертаємо заглушку відразу
    try:
        if not r2_object_exists(file_key):
            logger.debug("R2 content not found for %s, returning default", file_key)
            return default
    except Exception:
        logger.exception("Помилка при перевірці існування об'єкта в R2 для %s", file_key)

    try:
        s3 = get_s3_client()
        obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return obj["Body"].read().decode("utf-8")
    except Exception as e:
        logger.warning("Не вдалося отримати контент з R2 для %s: %s", file_key, e)
        return default


def get_r2_object_if_exists(file_key):
    """
    Перевіряє, чи існує об'єкт з ключем `file_key` у R2. Якщо існує — повертає
    кортеж (content_str, size_bytes). Якщо не існує або сталася помилка — повертає (None, None).

    Args:
        file_key (str): Ключ об'єкта в бакеті (наприклад, 'bins/bin_abc.txt')

    Returns:
        tuple: (content:str, size:int) або (None, None)
    """
    s3 = get_s3_client()
    try:
        head = s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '')
        # Типові коди для неіснуючого об'єкта: '404', 'NoSuchKey', 'NotFound'
        if code in ('404', 'NoSuchKey', 'NotFound'):
            logger.debug("R2 object not found: %s", file_key)
            return None, None
        logger.warning("ClientError checking R2 for %s: %s", file_key, e)
        return None, None
    except Exception as e:
        logger.warning("Unexpected error checking R2 for %s: %s", file_key, e)
        return None, None

    # Якщо head_object успішний — отримуємо сам об'єкт
    try:
        obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        body = obj['Body'].read()
        try:
            content = body.decode('utf-8')
        except Exception:
            # Якщо не текстовий — повертаємо байти як None (або можна вернути body)
            content = None
        size = int(head.get('ContentLength', len(body)))
        return content, size
    except Exception as e:
        logger.warning("Failed to get R2 object %s after head_object: %s", file_key, e)
        return None, None


def r2_object_exists(file_key):
    """
    Перевіряє наявність об'єкта у R2 за ключем. Повертає True якщо об'єкт існує, інакше False.
    """
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return True
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '')
        if code in ('404', 'NoSuchKey', 'NotFound'):
            return False
        logger.warning("ClientError checking existence for %s: %s", file_key, e)
        return False
    except Exception as e:
        logger.warning("Error checking existence for %s: %s", file_key, e)
        return False

def get_bin_size(file_key):
    """
    Повертає розмір файлу (біна) у байтах з Cloudflare R2.
    
    Args:
        file_key (str): Ключ файлу в R2 бакеті
    
    Returns:
        int or None: Розмір файлу в байтах або None при помилці
    """
    # Якщо об'єкт не існує — повертаємо 0
    try:
        if not r2_object_exists(file_key):
            logger.debug("R2 object %s does not exist, returning size 0", file_key)
            return 0
    except Exception:
        logger.exception("Помилка при перевірці існування об'єкта в R2 для %s", file_key)

    s3 = get_s3_client()
    try:
        obj = s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return obj['ContentLength']
    except Exception as e:
        logger.warning("Не вдалося отримати розмір з R2 for %s: %s", file_key, e)
        return None


def delete_from_r2(file_key):
    """
    Видаляє файл з Cloudflare R2 за ключем.
    
    Args:
        file_key (str): Ключ файлу для видалення
    
    Returns:
        bool: True якщо видалено успішно, False при помилці
    """
    # Якщо нема об'єкта — повертаємо False (нічого не видалено)
    try:
        if not r2_object_exists(file_key):
            logger.debug("delete_from_r2: object %s not found, skipping delete", file_key)
            return False
    except Exception:
        logger.exception("Помилка при перевірці існування об'єкта перед видаленням %s", file_key)

    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return True
    except Exception as e:
        logger.warning("Помилка при видаленні з R2 для %s: %s", file_key, e)
        return False

def smart_search(query):
    """
    Розумний fuzzy-пошук бінів по назві та мові за допомогою RapidFuzz.
    
    Args:
        query (str): Пошуковий запит
    
    Returns:
        QuerySet: Відфільтрований і відсортований QuerySet бінів із схожістю > 50%
    
    Notes:
        Використовує fuzz.partial_ratio для порівняння запиту з title та language_display
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
    Кешує метадані та контент біна у Redis для оптимізації швидкості доступу.
    
    Args:
        bin (Create_Bins): Об'єкт біна для кешування
        bin_content (str, optional): Текстовий контент біна, якщо None - контент не кешується
        ttl_meta (int): Час життя кешу метаданих у секундах (за замовчуванням 3600 = 1 година)
        ttl_content (int): Час життя кешу контенту у секундах (за замовчуванням 3600 = 1 година)
    
    Notes:
        Зберігає метадані як JSON у ключі bin_meta:<hash>
        Зберігає контент у ключі bin_content:<hash>
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
    Видаляє кеш метаданих і контенту біна з Redis при оновленні або видаленні.
    
    Args:
        hash (str): Хеш біна для інвалідації кешу
    
    Notes:
        Видаляє обидва ключі: bin_meta:<hash> та bin_content:<hash>
    """
    redis_cache = get_redis_client()
    meta_key = f"bin_meta:{hash}"
    content_key = f"bin_content:{hash}"
    redis_cache.delete(meta_key)
    redis_cache.delete(content_key)
