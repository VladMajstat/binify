# from django.apps import AppConfig

# class BinsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'bins'
#     verbose_name = "Створити_Bin"

#     def ready(self):
#         from bins.tasks import delete_expired_bins_task
#         delete_expired_bins_task(repeat=3600)  # запускати кожну годину

        #python manage.py process_tasks