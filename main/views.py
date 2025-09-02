# from django.http import HttpResponse
from django.shortcuts import render

def main(request):
    context = {
        "title": "Binify — Головна",
        "content": "Легко зберігай та ділись фрагментами коду або тексту.",
        "create_new_bin": "Створити новий Bin",
        "last_bin": "Останні Bin",
        "0_bins": "Немає жодного біна. Будь першим!",
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
