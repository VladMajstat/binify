from django.db import models
from django.contrib.auth import get_user_model
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES

class Create_Bins(models.Model):
    file_url = models.URLField(blank=True, null=True, verbose_name="Посилання на файл")
    content = models.TextField(verbose_name="Вміст", help_text="Введіть текст для збереження у bin")
    category = models.CharField(max_length=50, blank=True, choices=CATEGORY_CHOICES, default='NONE', verbose_name="Категорія", help_text="Виберіть категорію для bin")
    tags = models.CharField(max_length=200, blank=True, verbose_name="Теги", help_text="Введіть теги через кому для кращої організації")
    language = models.CharField(max_length=50, blank=True, choices=LANGUAGE_CHOICES, default='none', verbose_name="Мова", help_text="Виберіть мову для підсвітки синтаксису")
    expiry = models.CharField(max_length=50, choices=EXPIRY_CHOICES, default='never', verbose_name="Термін дії", help_text="Виберіть, коли цей bin має бути видалений",)
    expiry_at = models.DateTimeField(null=True, blank=True, verbose_name="Bin видаляється після")
    access = models.CharField(max_length=50, choices=ACCESS_CHOICES, default='public', verbose_name="Доступність", help_text="Виберіть, яким буде цей bin, публічним або приватним",)
    title = models.CharField(max_length=150, blank=True, verbose_name="Назва")
    author = models.ForeignKey(
        get_user_model(),  # Динамічно отримує модель користувача
        on_delete=models.SET_NULL,  # Якщо користувача видалено — поле стає NULL 
        null=True, 
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    # def __str__(self):
    #     """Повертає рядкове представлення об'єкта (назва або частина вмісту)"""
    #     return self.title or self.content[:30]

    class Meta:
        db_table = 'create_bin'
        verbose_name = "Bin"
        verbose_name_plural = "Bins"


# class ViewBin(models.Model):
    