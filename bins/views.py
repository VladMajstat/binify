from django.shortcuts import render, redirect
from .forms import CreateBinsForm
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES
import uuid
from .models import Create_Bins
from django.contrib import messages
from .utils import upload_to_r2, get_expiry_map

# логіка для створення нового bin.
def create_bin(request):
    if request.method == "POST":
        # Створюємо форму з даними, які надіслав користувач
        form = CreateBinsForm(request.POST)
        # Перевіряємо валідність даних
        if form.is_valid():
            try:
                data = form.cleaned_data
                # Генеруємо унікальне ім'я файлу для Bin
                filename = f"bins/bin_{uuid.uuid4().hex}.txt"
                # Завантажуємо контент у Cloudflare R2
                file_url = upload_to_r2(filename, data['content'])
                # Визначаємо дату видалення Bin
                expiry_at = get_expiry_map(data['expiry'])
                # Створюємо Bin у базі даних
                Create_Bins.objects.create(
                    file_url=file_url,
                    category=data['category'],
                    language=data['language'],
                    expiry=data['expiry'],
                    expiry_at=expiry_at,
                    access=data['access'],
                    title=f"{request.user.username}/{data['title']}",
                    tags=data['tags'],
                    author=request.user,
                )
                messages.success(request, "Bin успішно створено!")
                return redirect("main:index")
            except Exception as e:
                print(f"Помилка при створенні bin: {e}")
                messages.error(request, "❗ Не вдалося створити Bin. Спробуйте ще раз.")
                return redirect("main:index")
        else:
            # Якщо дані невалідні — показуємо помилку
            messages.error(request, "❗ Дані форми некоректні. Перевірте введене!")
    else:
        # Якщо GET-запит — створюємо порожню форму
        form = CreateBinsForm()

    # Передаємо форму та choices у шаблон для рендерингу
    context = {
        "title": "Створити Bin — Binify",
        "content": "Створити новий Bin",
        "form": form,
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
