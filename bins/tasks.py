from bins.models import Create_Bins
from bins.utils import delete_from_r2
from django.utils import timezone


def delete_expired_bins():
    """Helper that immediately deletes expired bins (callable from tests).

    Note: previously this project used `django-background-tasks` and a
    scheduled wrapper. That dependency was removed and scheduling should be
    handled by an external scheduler or a management command if needed.
    """
    now = timezone.now()
    expired_bins = Create_Bins.objects.filter(expiry_at__isnull=False, expiry_at__lt=now)
    for bin in expired_bins:
        delete_from_r2(bin.file_key)
        bin.delete()