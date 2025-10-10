from background_task import background
from bins.models import Create_Bins
from bins.utils import delete_from_r2
from django.utils import timezone

@background(schedule=60)  # запуск через 1 хвилину після реєстрації
def delete_expired_bins_task():
    now = timezone.now()
    expired_bins = Create_Bins.objects.filter(expiry_at__isnull=False, expiry_at__lt=now)
    for bin in expired_bins:
        delete_from_r2(bin.file_key)
        bin.delete()