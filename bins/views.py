from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
import boto3
from django.conf import settings
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES
import uuid
from .models import Create_Bins
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone

# логіка для створення нового bin.
@login_required()
def create_bin(request):

    if request.method == "POST":
        try:
            content = request.POST.get('content')
            category = request.POST.get('category')
            language = request.POST.get('language')
            expiry = request.POST.get('expiry')
            access = request.POST.get('access')
            title = request.POST.get('title')
            tags = request.POST.get('tags')

            # Генерує унікальне ім’я файлу для bin
            filename = f"bins/bin_{uuid.uuid4().hex}.txt"

            # Підключення до R2
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            # Завантаження файлу
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=filename,
                Body=content,
                ContentType='text/plain'
            )

            file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{filename}"

            EXPIRY_MAP = {
                "never": None,
                "1m": timedelta(minutes=1),
                "1h": timedelta(hours=1),
                "12h": timedelta(hours=12),
                "1d": timedelta(days=1),
                "1w": timedelta(weeks=1),
                "2w": timedelta(weeks=2),
                "30d": timedelta(days=30),
                "6mo": timedelta(days=30 * 6),
                "1y": timedelta(days=365),
            }

            expiry_at = None
            if expiry in EXPIRY_MAP and EXPIRY_MAP[expiry]:
                expiry_at = timezone.now() + EXPIRY_MAP[expiry]


            # Зберігаємо Bin у БД
            Create_Bins.objects.create(
                file_url=file_url,
                category=category,
                language=language,
                expiry=expiry,
                expiry_at=expiry_at,
                access=access,
                title=f"{request.user.username}/{title}",
                tags=tags,
                author=request.user,
            )

            # Редірект на сторінку перегляду bin
            return redirect("main:index")
        except Exception as e:
            print(f"Помилка при створенні bin: {e}")
            messages.error(request, "❗ Не вдалося створити Bin. Спробуйте ще раз.")
            return redirect("main:index")
    else:

        context = {
            "title": "Створити Bin — Binify",
            "content": "Створити новий Bin",
            "category_choices": CATEGORY_CHOICES,
            "language_choices": LANGUAGE_CHOICES,
            "expiry_choices": EXPIRY_CHOICES,
            "access_choices": ACCESS_CHOICES,
        }

        return render(request, "bins/create_bin.html", context)

# показує вміст конкретного bin за ідентифікатором або slug
def view_bin(request):
    context = {
        "title": "Перегляд Bin — Binify",
        "content": "Перегляд існуючого Bin",
    }
    return render(request, "bins/view_bin.html", context)

# дозволяє автору змінити вміст bin.
# def edit_bin(request):
#     context = {
#         "title": "Редагувати Bin — Binify",
#         "content": "Редагувати існуючий Bin",
#     }
#     return render(request, "bins/edit_bin.html", context)

# дозволяє видалити bin.
# def delete_bin(request):
#     context = {
#         "title": "Видалити Bin — Binify",
#         "content": "Видалити існуючий Bin",
#     }
#     return render(request, "bins/delete_bin.html", context)

# показує всі bin (або лише користувача, або загальні).
# def list_bins(request):
#     context = {
#         "title": "Список Bin — Binify",
#         "content": "Перегляд усіх Bin",
#     }
#     return render(request, "bins/list_bins.html", context)

# дозволяє шукати bin за ключовими словами або тегами.
# def search_bins(request):
#     context = {
#         "title": "Пошук Bin — Binify",
#         "content": "Пошук Bin за ключовими словами або тегами",
#     }
#     return render(request, "bins/search_bins.html", context)

# статистика переглядів/лайків bin.
# def bin_statistics(request):
#     context = {
#         "title": "Статистика Bin — Binify",
#         "content": "Перегляд статистики для Bin",
#     }
#     return render(request, "bins/bin_statistics.html", context)
