from django.core.management.base import BaseCommand
from bins.tasks import delete_expired_bins


class Command(BaseCommand):
    help = "Видаляє прострочені біни, викликаючи `bins.tasks.delete_expired_bins()`"

    def handle(self, *args, **options):
        try:
            result = delete_expired_bins()
            # delete_expired_bins() повертає True/False або None — просто повідомимо про виконання
            self.stdout.write(self.style.SUCCESS('delete_expired_bins executed successfully'))
        except Exception as e:
            self.stderr.write(f'Error running delete_expired_bins: {e}')
            raise
