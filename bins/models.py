from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES

class Create_Bins(models.Model):
    file_url = models.URLField(blank=True, null=True, verbose_name="Посилання на файл")
    file_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ключ файлу R2", help_text="Шлях до файлу у бакеті (наприклад, bins/bin_123.txt)")
    content = models.TextField(verbose_name="Вміст", help_text="Введіть текст для збереження у bin")
    category = models.CharField(max_length=50, blank=True, choices=CATEGORY_CHOICES, default='NONE', verbose_name="Категорія", help_text="Виберіть категорію для bin")
    tags = models.CharField(max_length=200, blank=True, verbose_name="Теги", help_text="Введіть теги через кому для кращої організації")
    language = models.CharField(max_length=50, blank=True, choices=LANGUAGE_CHOICES, default='none', verbose_name="Мова", help_text="Виберіть мову для підсвітки синтаксису")
    expiry = models.CharField(max_length=50, choices=EXPIRY_CHOICES, default='never', verbose_name="Термін дії", help_text="Виберіть, коли цей bin має бути видалений",)
    expiry_at = models.DateTimeField(null=True, blank=True, verbose_name="Bin видаляється після")
    access = models.CharField(max_length=50, choices=ACCESS_CHOICES, default='public', verbose_name="Доступність", help_text="Виберіть, яким буде цей bin, публічним або приватним",)
    title = models.CharField(max_length=150, blank=True, verbose_name="Назва")
    size_bin = models.PositiveIntegerField(default=0, verbose_name="Розмір (байт)", help_text="Розмір вмісту в байтах")
    author = models.ForeignKey(
        get_user_model(),  # Динамічно отримує модель користувача
        on_delete=models.SET_NULL,  # Якщо користувача видалено — поле стає NULL 
        null=True, 
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Кількість лайків")
    dislikes_count = models.PositiveIntegerField(default=0, verbose_name="Кількість дизлайків")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Кількість переглядів")
    hash = models.CharField(max_length=64, unique=True, blank=True, null=True, verbose_name="Hash", help_text="SHA-256 хеш вмісту для унікальності")

    class Meta:
        db_table = 'create_bin'
        verbose_name = "Bin"
        verbose_name_plural = "Bins"

    # Повертає рядкове представлення об'єкта (назва або частина вмісту)
    def __str__(self):
        return f"{self.title}"

    def is_active(self):
        return self.expiry_at is None or self.expiry_at > timezone.now()


# Модель для збереження переглядів бінів
class ViewBin(models.Model):
    bin = models.ForeignKey(Create_Bins, on_delete=models.CASCADE, related_name="views")  # Зв'язок з біном
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)  # Користувач, який переглянув
    ip_address = models.CharField(max_length=45, blank=True)  # IP-адреса переглядача
    viewed_at = models.DateTimeField(auto_now_add=True)  # Дата перегляду
    user_agent = models.CharField(max_length=256, blank=True)  # User-Agent браузера
    session_key = models.CharField(max_length=40, blank=True)  # Сесія для унікальності перегляду

    class Meta:
        ordering = ["-viewed_at"]  # Сортування: нові перегляди першими


class BinLike(models.Model):
    bin = models.ForeignKey(Create_Bins, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    is_like = models.BooleanField(default=True)  # True=лайк, False=дизлайк
    created_at = models.DateTimeField(auto_now_add=True)

class BinComment(models.Model):
    bin = models.ForeignKey(Create_Bins, on_delete=models.CASCADE, related_name="comments")  # звʼязок з біном
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)  # автор коментаря
    text = models.TextField(verbose_name="Текст коментаря")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Коментар"
        verbose_name_plural = "Коментарі"

    def __str__(self):
        return f"{self.author}: {self.text[:30]}"
