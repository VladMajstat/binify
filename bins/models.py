from django.db import models
from django.contrib.auth import get_user_model
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES

class Create_Bins(models.Model):
    # Основний вміст bin (код або текст)
    content = models.TextField(verbose_name="Вміст", help_text="Введіть текст для збереження у bin")

    # Категорія bin
    category = models.CharField(
        max_length=50,
        blank=True,
        choices=CATEGORY_CHOICES,
        default='NONE',
        verbose_name="Категорія",
        help_text="Виберіть категорію для bin"
        )

    # Теги
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Теги", 
        help_text="Введіть теги через кому для кращої організації"
        )

    #мова
    language = models.CharField(
        max_length=50,
        blank=True,
        choices=LANGUAGE_CHOICES,
        default='none',
        verbose_name="Мова",
        help_text="Виберіть мову для підсвітки синтаксису"
    )

    # Термін дії bin
    expiry = models.CharField(
        max_length=50,
        choices=EXPIRY_CHOICES,
        default='never',
        verbose_name="Термін дії",
        help_text="Виберіть, коли цей bin має бути видалений",
    )

    # Доступність bin
    access = models.CharField(
        max_length=50,
        choices=ACCESS_CHOICES,
        default='public',
        verbose_name="Доступність",
        help_text="Виберіть, яким буде цей bin, публічним або приватним",
    )

    # Назва bin (необов'язково)
    title = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Назва"
    )

    # Автор bin (зв'язок з користувачем)
    author = models.ForeignKey(
        get_user_model(),  # Динамічно отримує модель користувача
        on_delete=models.SET_NULL,  # Якщо користувача видалено — поле стає NULL
        null=True,  # Дозволяє зберігати NULL   
        verbose_name="Автор"
    )

    # Дата створення bin
    created_at = models.DateTimeField(
        auto_now_add=True,  # Автоматично встановлює дату при створенні
        verbose_name="Створено"
    )

    # Дата останнього оновлення bin
    updated_at = models.DateTimeField(
        auto_now=True,  # Автоматично оновлює дату при кожному збереженні
        verbose_name="Оновлено"
    )

    # Унікальний ідентифікатор для красивих URL (опціонально)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        null=True,
        verbose_name="URL"
    )

    # def __str__(self):
    #     """Повертає рядкове представлення об'єкта (назва або частина вмісту)"""
    #     return self.title or self.content[:30]

    class Meta:
        db_table = 'create_bin'
        verbose_name = "Bin"
        verbose_name_plural = "Bins"
    # class Meta:
    #     verbose_name = "Bin"
    #     verbose_name_plural = "Bins"
    #     ordering = ["-created_at"]  # Сортування за датою створення (новіші першими)
