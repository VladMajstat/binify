import boto3
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from urllib.parse import urlparse

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


    # Отримує контент файлу з Cloudflare R2 через boto3 (для приватних бакетів).
def fetch_bin_content_from_r2(file_key):

    s3 = get_s3_client()
    try:
        obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
        return obj['Body'].read().decode('utf-8')
    except Exception as e:
        return f"Не вдалося отримати контент з R2: {e}"
