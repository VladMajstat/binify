from django.apps import AppConfig


class BinsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bins"
    verbose_name = "Створити_Bin"

    def ready(self):
        # Плануємо щоденне очищення прострочених бінів (перше спрацювання через 60 c)
        from bins.tasks import delete_expired_bins_task

        # repeat=86400 → кожні 24 години; задачі виконуються процесом `manage.py process_tasks`
        delete_expired_bins_task(repeat=86400)