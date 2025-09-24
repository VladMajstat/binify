import boto3
import uuid
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

from bins.models import Create_Bins

def create_bin_from_data(request, data):
    try:
        filename = f"bins/bin_{uuid.uuid4().hex}.txt"
        file_url = upload_to_r2(filename, data["content"])
        expiry_at = get_expiry_map(data["expiry"])
        file_key = filename
        size_bin = get_bin_size(file_key)
        Create_Bins.objects.create(
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
