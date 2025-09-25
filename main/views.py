# from django.http import HttpResponse
from django.shortcuts import render
from bins.models import Create_Bins
from bins.views import q_search
from django.core.paginator import Paginator


def main(request):
    # Отримуємо пошуковий запит з параметрів GET (якщо був)
    query = request.GET.get("q", None)
    # Отримуємо номер сторінки для пагінації (за замовчуванням 1)
    page_number = int(request.GET.get("page", 1))

    # Якщо є пошуковий запит, викликаємо функцію пошуку
    if query:
        bins_list = q_search(query)
        search_message = f'Результати пошуку для: "{query}"'
    else:
        # Якщо пошуку немає, отримуємо всі біни, новіші зверху
        bins_list = Create_Bins.objects.all().order_by("-created_at")
        search_message = None

    # На першій сторінці показуємо 12 бінів, на наступних — по 24
    per_page = 12 if page_number == 1 else 24
    # Створюємо пагінатор для списку бінів
    paginator = Paginator(bins_list, per_page)
    # Отримуємо біни для поточної сторінки
    bins = paginator.get_page(page_number)

    context = {
        "title": "Binify — Головна",
        "content": "Легко зберігай та ділись фрагментами коду або тексту.",
        "create_new_bin": "Створити новий Bin",
        "last_bin": "Останні Bin",
        "0_bins": "Немає жодного біна. Будь першим!",
        "bins": bins,
        "search_message": search_message,
        "show_more": bins.has_next(),  # Чи є ще сторінки для пагінації
        "next_page": (bins.next_page_number() if bins.has_next() else None),  # Номер наступної сторінки
        "query": query, 
    }

    return render(request, 'main/main.html', context)

def about(request):
    context = {
        "title": "Про сайт",
        "content": "Даний сайт створено для демонстрації можливостей Django. Тут ви можете створювати, переглядати та редагувати свої 'бін'-об'єкти.",
    }

    return render(request, 'main/about.html', context)
