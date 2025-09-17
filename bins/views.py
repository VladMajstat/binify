from django.shortcuts import render
from .forms import CreateBinsForm
from django.http import HttpResponseRedirect
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES
import uuid
from .models import Create_Bins, BinLike
from django.contrib import messages
from .utils import upload_to_r2, get_expiry_map, fetch_bin_content_from_r2
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


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
                # Додаємо ключ файлу (шлях у бакеті)
                file_key = filename
                # Створюємо Bin у базі даних
                Create_Bins.objects.create(
                    file_url=file_url,
                    file_key=file_key,
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
                return HttpResponseRedirect("main:index")
            except Exception as e:
                print(f"Помилка при створенні bin: {e}")
                messages.error(request, "❗ Не вдалося створити Bin. Спробуйте ще раз.")
                return HttpResponseRedirect("main:index")
        else:
            # Якщо дані невалідні — показуємо помилку
            messages.error(request, "❗ Дані форми некоректні. Перевірте введене!")
    else:
        # Якщо GET-запит — створюємо порожню форму
        form = CreateBinsForm()

    # Передаємо форму та choices у шаблон для рендерингу
    content = {
        "title": "Створити Bin — Binify",
        "content": "Створити новий Bin",
        "form": form,
        "category_choices": CATEGORY_CHOICES,
        "language_choices": LANGUAGE_CHOICES,
        "expiry_choices": EXPIRY_CHOICES,
        "access_choices": ACCESS_CHOICES,
    }
    return render(request, "bins/create_bin.html", content)

# показує вміст конкретного bin за ідентифікатором або slug
def view_bin(request, id):
    bin = get_object_or_404(Create_Bins, pk=id)

    # --- Отримання контенту з R2 ---
    bin_content = None
    if bin.file_url:
        try:
            bin_content = fetch_bin_content_from_r2(bin.file_key)
        except Exception as e:
            bin_content = "Не вдалося отримати контент з R2."
            print(f"Помилка: {e}")
    else:
        bin_content = "Контент не знайдено."

    content = {
        "title": f"Перегляд Bin — {bin.title}",
        "content": "Перегляд існуючого Bin",
        'bin': bin,
        'bin_content': bin_content,
    }
    return render(request, "bins/view_bin.html", content)

def user_bins(request):
    # Отримуємо всі біни, створені поточним користувачем
    bins = Create_Bins.objects.filter(author=request.user).order_by('-created_at')
    
    content = {
        'title': 'Мої Bin',
        'bins': bins,
    }
    return render(request, 'bins/user_bins.html', content)


# Повертає кількість лайків/дизлайків для біна (GET) або додає лайк/дизлайк (POST).
def likes_dislikes_bins(request, id):
    # Отримуємо бін за id
    bin = get_object_or_404(Create_Bins, pk=id)
    # Визначаємо користувача (або None для анонімного)
    user = request.user if request.user.is_authenticated else None

    if request.method == "POST":
        # Отримуємо тип реакції (лайк чи дизлайк) з POST-запиту
        is_like = request.POST.get('is_like') == 'true'
        # Шукаємо існуючий лайк/дизлайк для цього біна і користувача
        like_obj = BinLike.objects.filter(bin=bin, user=user).first()
        if like_obj:
            # Якщо запис існує — оновлюємо реакцію
            like_obj.is_like = is_like
            like_obj.save()
        else:
            # Якщо запису немає — створюємо новий лайк/дизлайк
            BinLike.objects.create(bin=bin, user=user, is_like=is_like)

    # Підраховуємо кількість лайків і дизлайків для біна
    likes = bin.likes.filter(is_like=True).count()
    dislikes = bin.likes.filter(is_like=False).count()
    bin.likes_count = likes
    bin.dislikes_count = dislikes
    bin.save(update_fields=["likes_count", "dislikes_count"])
    # Повертаємо дані у форматі JSON для AJAX
    return JsonResponse({'likes': likes, 'dislikes': dislikes})

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


# дозволяє шукати bin за ключовими словами або тегами.
# def search_bins(request):
#     context = {
#         "title": "Пошук Bin — Binify",
#         "content": "Пошук Bin за ключовими словами або тегами",
#     }
#     return render(request, "bins/search_bins.html", context)
