from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES
from .models import Create_Bins, BinLike
from .utils import (
    upload_to_r2,
    create_bin_from_data,
    delete_from_r2,
    get_bin_content,
)
from .forms import CreateBinsForm, BinCommentForm, BinComment

def create_bin(request):
    if request.method == "POST":
        form = CreateBinsForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                request.session['pending_bin_data'] = form.cleaned_data
                messages.info(request, "Для створення Bin потрібно увійти або зареєструватися.")
                return redirect("users:login")
            else:
                success = create_bin_from_data(request, form.cleaned_data)
                if success:
                    messages.success(request, "Bin успішно створено!")
                    return redirect("bins:index")
                else:
                    messages.error(request, "❗ Не вдалося створити Bin. Спробуйте ще раз.")
        else:
            messages.error(request, "❗ Дані форми некоректні. Перевірте введене!")
    else:
        form = CreateBinsForm()

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
    bin_content = get_bin_content(bin)
    # Отримуємо всі коментарі для цього Bin
    comments = bin.comments.all().order_by('-created_at')
    form = CreateBinsForm(instance=bin)

    context = {
        "title": f"Перегляд Bin — {bin.title}",
        "content": "Перегляд існуючого Bin",
        "bin": bin,
        'form': form,
        "bin_content": bin_content,
        "comments": comments,
        "views_count": bin.views_count,
        "category_choices": CATEGORY_CHOICES,
        "language_choices": LANGUAGE_CHOICES,
        "expiry_choices": EXPIRY_CHOICES,
        "access_choices": ACCESS_CHOICES,
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

def edit_bin(request, id):
    bin = get_object_or_404(Create_Bins, pk=id, author=request.user)
    # Отримуємо поточний контент з R2 для відображення у формі
    bin_content = get_bin_content(bin)

    if request.method == "POST":
        form = CreateBinsForm(request.POST, instance=bin)
        if form.is_valid():
            # Перевіряємо, чи змінився контент
            new_content = form.cleaned_data.get("content")
            if new_content and new_content != bin_content:
                # Оновлюємо контент у R2
                upload_to_r2(bin.file_key, new_content)
            form.save()
            messages.success(request, "Bin успішно оновлено!")
            return redirect("bins:view_bin", id=bin.id)
        else:
            messages.error(request, "❗ Дані форми некоректні. Перевірте введене!")
    else:
        # Передаємо поточний контент у форму для відображення
        form = CreateBinsForm(instance=bin, initial={"content": bin_content})

    context = {
        "bin": bin,
        "form": form,
        "bin_content": bin_content,
        "category_choices": CATEGORY_CHOICES,
        "language_choices": LANGUAGE_CHOICES,
        "expiry_choices": EXPIRY_CHOICES,
        "access_choices": ACCESS_CHOICES,
    }

    return render(request, "bins/view_bin.html", context=context)

def delete_bin(request, id):
    bin = get_object_or_404(Create_Bins, pk=id, author=request.user)
    if request.method == "POST":
        # Видалити файл з R2
        delete_from_r2(bin.file_key)
        # Видалити бін з бази
        bin.delete()
        messages.success(request, "Bin успішно видалено!")
        return redirect("bins:view_bin")
    return redirect("bins:view_bin", id=bin.id)


# дозволяє шукати bin за ключовими словами або тегами.
# def search_bins(request):
#     context = {
#         "title": "Пошук Bin — Binify",
#         "content": "Пошук Bin за ключовими словами або тегами",
#     }
#     return render(request, "bins/search_bins.html", context)
