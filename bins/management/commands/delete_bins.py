import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from bins.models import Create_Bins
from django.utils import timezone


class Command(BaseCommand):
    help = "Видаляє прострочені bin разом із файлами у Cloudflare"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_bins = Create_Bins.objects.filter(
            expiry_at__isnull=False, expiry_at__lt=now
        )
        count = 0

        # Підключення до Cloudflare R2 (або S3)
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        for bin in expired_bins:
            # Витягуємо ключ файлу з file_url
            key = bin.file_url.split("/")[-1]
            try:
                s3.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f"bins/{key}"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Не вдалося видалити файл для bin {bin.pk}: {e}"
                    )
                )
            bin.delete()
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Видалено {count} прострочених bin і їх файли")
        )


# Create_Bins.objects.filter(
#     models.Q(expiry_at__isnull=True) | models.Q(expiry_at__gt=timezone.now())
# )