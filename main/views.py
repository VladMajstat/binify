# from django.http import HttpResponse
from django.shortcuts import render
from bins.models import Create_Bins
from bins.views import q_search
from django.core.paginator import Paginator

def main(request):
    query = request.GET.get('q', None)
    if query:
        bins = q_search(query)
        search_message = f'Результати пошуку для: "{query}"'
    else:
        bins = Create_Bins.objects.all().order_by('-created_at')
        search_message = None

    context = {
        "title": "Binify — Головна",
        "content": "Легко зберігай та ділись фрагментами коду або тексту.",
        "create_new_bin": "Створити новий Bin",
        "last_bin": "Останні Bin",
        "0_bins": "Немає жодного біна. Будь першим!",
        "bins": bins,
        "search_message": search_message,
    }

    return render(request, 'main/main.html', context)

def view_bin(request):
    context = {
        "title": "Перегляд Bin — Binify",
    }

    return render(request, 'main/view_bin.html', context)

def about(request):
    context = {
        "title": "Про сайт",
        "content": "Даний сайт створено для демонстрації можливостей Django. Тут ви можете створювати, переглядати та редагувати свої 'бін'-об'єкти.",
    }

    return render(request, 'main/about.html', context)
