from django.shortcuts import render
from django.shortcuts import redirect
import uuid
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES
from .models import Create_Bins, BinLike
from .utils import upload_to_r2, get_expiry_map, fetch_bin_content_from_r2, get_bin_size
from .forms import CreateBinsForm, BinCommentForm, BinComment


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
                #Отримуємо розмір Bin
                size_bin = get_bin_size(file_key)
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
                    size_bin=size_bin,
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
    return render(request, "bins/create_bin.html", context=context)

# показує вміст конкретного bin за ідентифікатором або slug
def view_bin(request, id):

    bin = get_object_or_404(Create_Bins, pk=id)

    # --- Підрахунок переглядів ---
    # 1. Отримуємо session_key для унікальності перегляду
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    # 2. Перевіряємо, чи вже був перегляд з цим session_key/user
    already_viewed = bin.views.filter(session_key=session_key).exists()
    # 3. Визначаємо користувача (авторизований чи ні)
    user = request.user if request.user.is_authenticated else None
    if user:
        already_viewed = bin.views.filter(user=user).exists() or already_viewed
    # 4. Якщо перегляд унікальний — додаємо запис у ViewBin
    if not already_viewed:
        bin.views.create(
            user=user,  # Користувач (або None)
            ip_address=request.META.get('REMOTE_ADDR', ''),  # IP-адреса
            user_agent=request.META.get('HTTP_USER_AGENT', ''),  # User-Agent браузера
            session_key=session_key  # Сесія для унікальності
        )
        # 5. Оновлюємо кількість переглядів у моделі Create_Bins
        bin.views_count = bin.views.count()
        bin.save(update_fields=["views_count"])

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

    # Отримуємо всі коментарі для цього Bin
    comments = bin.comments.all().order_by('-created_at')

    context = {
        "title": f"Перегляд Bin — {bin.title}",
        "content": "Перегляд існуючого Bin",
        "bin": bin,
        "bin_content": bin_content,
        "comments": comments,  # Передаємо коментарі у шаблон
        "views_count": bin.views_count,
    }
    return render(request, "bins/view_bin.html", context=context)

def user_bins(request):
    # Отримуємо всі біни поточного користувача
    bins = Create_Bins.objects.filter(author=request.user).order_by('-created_at')
    # Фільтруємо лише активні біни через метод is_active
    bins = [bin for bin in bins if bin.is_active()]

    context = {
        'title': 'Мої Bin',
        'bins': bins,
    }
    return render(request, "bins/user_bins.html", context=context)


def user_comments(request):
    # Отримуємо всі коментарі, створені поточним користувачем
    comments = BinComment.objects.filter(author=request.user).order_by("-created_at")
    context = {
        "title": "Мої коментарі",
        "comments": comments,
    }
    return render(request, "bins/user_comments.html", context=context)

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


def bin_comment(request, id):
    # Отримуємо Bin за id (перевіряємо, чи існує)
    bin = get_object_or_404(Create_Bins, pk=id)
    if request.method == "POST":
        # Створюємо форму коментаря з POST-даних
        form = BinCommentForm(request.POST)
        if form.is_valid():
            # Створюємо екземпляр коментаря, але не зберігаємо у базі
            comment = form.save(commit=False)
            # Прив'язуємо коментар до Bin
            comment.bin = bin
            if request.user.is_authenticated:
                # Якщо користувач авторизований — зберігаємо автора
                comment.author = request.user
            else:
                return JsonResponse({'success': False, 'error': 'Тільки авторизовані користувачі можуть залишати коментарі.'})
            # Зберігаємо коментар у базі
            comment.save()
            # Рендеримо HTML для нового коментаря
            comment_html = render_to_string('bins/bin_comment.html', {'comment': comment})
            return JsonResponse({'success': True, 'comment_html': comment_html})
        else:
            error = form.errors.as_text()
            return JsonResponse({'success': False, 'error': error})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


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
