from django.shortcuts import render

# логіка для створення нового bin.
def create_bin(request):
    context = {
        "title": "Створити Bin — Binify",
        "content": "Створити новий Bin",
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