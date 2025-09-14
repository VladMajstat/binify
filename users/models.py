from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    image = models.ImageField(upload_to='users_images', blank=True, null=True, verbose_name='Аватар')
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')

    class Meta:
        db_table = 'user'
        verbose_name = "Користувача"
        verbose_name_plural = "Користувачі"

    #Повертає рядкове представлення об'єкта (назва або частина вмісту)
    def __str__(self):
        return self.username
